from uuid import UUID

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import (
    LecturerPublicationResponse,
    PublicationCreateRequest,
    PublicationListItemResponse,
    PublicationListQuery,
    PublicationUpdateRequest,
    PublicationUpdateResponse,
)
from app.v2.models.publication import Publication


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

    def create_publication(self, data: PublicationCreateRequest) -> PublicationListItemResponse:
        try:
            if data.doi is not None and self.publication_dao.get_by_doi(data.doi) is not None:
                raise ConflictError("Publication DOI already exists")

            publication = self.publication_dao.add(Publication(**data.model_dump()))
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
        self, publication_id: int, data: PublicationUpdateRequest
    ) -> PublicationUpdateResponse:
        try:
            publication = self.publication_dao.get_by_id(publication_id)
            if publication is None:
                raise NotFoundError("Publication not found")

            values = data.model_dump(exclude_unset=True)
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

    def delete_publication(self, publication_id: int) -> None:
        try:
            publication = self.publication_dao.get_by_id(publication_id)
            if publication is None:
                raise NotFoundError("Publication not found")

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
