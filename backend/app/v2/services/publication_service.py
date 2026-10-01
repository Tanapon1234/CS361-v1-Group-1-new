from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.core.exceptions import ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationListItemResponse,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateRequest,
)


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

    def create_publication(self, data: PublicationCreateRequest) -> PublicationResponse:
        raise NotImplementedError  # TODO: also save authors (data.lecturer_ids)

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
