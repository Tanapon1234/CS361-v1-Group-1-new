from uuid import UUID

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageResponse
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationCreateResponse,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateRequest,
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

    def list_publications(self, query: PublicationListQuery) -> PageResponse[PublicationResponse]:
        raise NotImplementedError  # TODO

    def create_publication(self, data: PublicationCreateRequest) -> PublicationCreateResponse:
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

        return PublicationCreateResponse.model_validate(publication)

    def get_publication(self, publication_id: int) -> PublicationResponse:
        raise NotImplementedError  # TODO

    def update_publication(
        self, publication_id: int, data: PublicationUpdateRequest
    ) -> PublicationResponse:
        raise NotImplementedError  # TODO

    def delete_publication(self, publication_id: int) -> None:
        raise NotImplementedError  # TODO

    def list_lecturer_publications(
        self, lecturer_id: UUID, query: PublicationListQuery
    ) -> PageResponse[PublicationResponse]:
        raise NotImplementedError  # TODO
