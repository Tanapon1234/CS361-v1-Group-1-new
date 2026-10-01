from uuid import UUID

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageResponse
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateRequest,
    PublicationUpdateResponse,
)


def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    if sqlstate == "23505":
        return True
    return "unique constraint failed" in str(exc.orig).lower()


class PublicationService:
    def __init__(self, publication_dao: PublicationDAO, lecturer_dao: LecturerDAO) -> None:
        self.publication_dao = publication_dao
        self.lecturer_dao = lecturer_dao

    def list_publications(self, query: PublicationListQuery) -> PageResponse[PublicationResponse]:
        raise NotImplementedError  # TODO

    def create_publication(self, data: PublicationCreateRequest) -> PublicationResponse:
        raise NotImplementedError  # TODO: also save authors (data.lecturer_ids)

    def get_publication(self, publication_id: int) -> PublicationResponse:
        raise NotImplementedError  # TODO

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
        raise NotImplementedError  # TODO

    def list_lecturer_publications(
        self, lecturer_id: UUID, query: PublicationListQuery
    ) -> PageResponse[PublicationResponse]:
        raise NotImplementedError  # TODO
