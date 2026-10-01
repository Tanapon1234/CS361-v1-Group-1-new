from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageResponse
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateRequest,
)


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
    ) -> PublicationResponse:
        raise NotImplementedError  # TODO

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
    ) -> PageResponse[PublicationResponse]:
        raise NotImplementedError  # TODO
