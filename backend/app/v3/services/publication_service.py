from uuid import UUID

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.v2.models.enums import VerificationStatus
from app.v2.models.publication import Publication
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.dtos.common import PageMeta, PageResponse
from app.v3.dtos.publication_dto import (
    LecturerPublicationResponse,
    PublicationCreateRequest,
    PublicationListItemResponse,
    PublicationListQuery,
    PublicationUpdateRequest,
    PublicationUpdateResponse,
)
from app.v3.security import Actor, Role


def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    if sqlstate == "23505":
        return True
    return "unique constraint failed" in str(exc.orig).lower()


class PublicationService:
    def __init__(self, publication_dao: PublicationDAO, lecturer_dao: LecturerDAO) -> None:
        self.publication_dao = publication_dao
        self.lecturer_dao = lecturer_dao

    def list_publications(
        self, query: PublicationListQuery
    ) -> PageResponse[PublicationListItemResponse]:
        try:
            publications, total = self.publication_dao.find_page(
                q=query.q,
                publication_year=query.publication_year,
                lecturer_id=None,
                limit=query.limit,
                offset=query.offset,
            )
        except OperationalError as exc:
            raise ServiceUnavailableError("Database is unreachable") from exc

        return PageResponse[PublicationListItemResponse](
            items=[
                PublicationListItemResponse.model_validate(publication)
                for publication in publications
            ],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_publication(
        self, data: PublicationCreateRequest, *, actor: Actor
    ) -> PublicationListItemResponse:
        if not actor.has_any(Role.STAFF) and actor.lecturer_id not in data.lecturer_ids:
            raise ForbiddenError("Add yourself to lecturer_ids: you can only add your own work")
        try:
            if data.doi is not None and self.publication_dao.get_by_doi(data.doi) is not None:
                raise ConflictError("Publication DOI already exists")
            for lecturer_id in data.lecturer_ids:
                if self.lecturer_dao.get_by_id(lecturer_id) is None:
                    raise NotFoundError(f"Lecturer {lecturer_id} not found")

            publication = self.publication_dao.add(
                Publication(**data.model_dump(exclude={"lecturer_ids"}))
            )
            if data.lecturer_ids:
                self.publication_dao.set_authors(publication.publication_id, data.lecturer_ids)
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Publication DOI already exists") from exc
            raise
        except OperationalError as exc:
            raise ServiceUnavailableError("Database is unreachable") from exc

        return PublicationListItemResponse.model_validate(publication)

    def get_publication(self, publication_id: int) -> PublicationListItemResponse:
        try:
            publication = self.publication_dao.get_by_id(publication_id)
        except OperationalError as exc:
            raise ServiceUnavailableError("Database is unreachable") from exc

        if publication is None:
            raise NotFoundError("Publication not found")

        return PublicationListItemResponse.model_validate(publication)

    def update_publication(
        self, publication_id: int, data: PublicationUpdateRequest, *, actor: Actor
    ) -> PublicationUpdateResponse:
        try:
            publication = self.publication_dao.get_by_id(publication_id)
            if publication is None:
                raise NotFoundError("Publication not found")
            self._require_author_or_staff(publication_id, actor)
            self._require_unlocked(publication, actor)

            values = data.model_dump(exclude_unset=True)
            if (
                values
                and not actor.has_any(Role.STAFF)
                and publication.verification_status is VerificationStatus.REJECTED
            ):
                # The author fixed it: back into the reviewers' queue
                values |= {
                    "verification_status": VerificationStatus.PENDING,
                    "verified_by": None,
                    "verified_at": None,
                }
            if "doi" in values and values["doi"] is not None:
                duplicate = self.publication_dao.get_by_doi(values["doi"])
                if duplicate is not None and duplicate.publication_id != publication_id:
                    raise ConflictError("Publication DOI already exists")

            updated = self.publication_dao.update(publication, values)
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Publication DOI already exists") from exc
            raise
        except OperationalError as exc:
            raise ServiceUnavailableError("Database is unreachable") from exc

        return PublicationUpdateResponse.model_validate(updated)

    def delete_publication(self, publication_id: int, *, actor: Actor) -> None:
        try:
            publication = self.publication_dao.get_by_id(publication_id)
            if publication is None:
                raise NotFoundError("Publication not found")
            self._require_author_or_staff(publication_id, actor)
            self._require_unlocked(publication, actor)

            self.publication_dao.delete(publication)
        except OperationalError as exc:
            raise ServiceUnavailableError("Database unavailable") from exc

    def list_lecturer_publications(
        self, lecturer_id: UUID, query: PublicationListQuery
    ) -> PageResponse[LecturerPublicationResponse]:
        try:
            if self.lecturer_dao.get_by_id(lecturer_id) is None:
                raise NotFoundError("Lecturer not found")

            rows, total = self.publication_dao.find_lecturer_page(
                lecturer_id,
                q=query.q,
                publication_year=query.publication_year,
                limit=query.limit,
                offset=query.offset,
            )
        except OperationalError as exc:
            raise ServiceUnavailableError("Database is unreachable") from exc

        items = [
            LecturerPublicationResponse(
                **PublicationListItemResponse.model_validate(publication).model_dump(),
                author_order=author_order,
            )
            for publication, author_order in rows
        ]
        return PageResponse[LecturerPublicationResponse](
            items=items,
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def _require_author_or_staff(self, publication_id: int, actor: Actor) -> None:
        if actor.has_any(Role.STAFF):
            return
        if actor.lecturer_id not in self.publication_dao.get_author_ids(publication_id):
            raise ForbiddenError("Only its authors or staff can change this publication")

    @staticmethod
    def _require_unlocked(publication: Publication, actor: Actor) -> None:
        if publication.verification_status is VerificationStatus.VERIFIED and not actor.has_any(
            Role.STAFF
        ):
            raise ForbiddenError("This publication is verified; ask staff to change it")
