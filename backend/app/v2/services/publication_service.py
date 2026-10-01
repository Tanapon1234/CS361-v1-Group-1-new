from uuid import UUID

from sqlalchemy.exc import OperationalError

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import (
    LecturerPublicationResponse,
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
    ) -> PublicationResponse:
        raise NotImplementedError  # TODO

    def delete_publication(self, publication_id: int) -> None:
        raise NotImplementedError  # TODO

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
