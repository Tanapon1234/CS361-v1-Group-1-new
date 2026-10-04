from uuid import UUID

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.publication_profile_dto import (
    PublicationProfileCreateRequest,
    PublicationProfileResponse,
    PublicationProfileUpdateRequest,
)


class PublicationProfileService:
    def __init__(
        self, publication_profile_dao: PublicationProfileDAO, lecturer_dao: LecturerDAO
    ) -> None:
        self.publication_profile_dao = publication_profile_dao
        self.lecturer_dao = lecturer_dao

    def list_publication_profiles(
        self, lecturer_id: UUID
    ) -> ListResponse[PublicationProfileResponse]:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        items = [
            PublicationProfileResponse.model_validate(item)
            for item in self.publication_profile_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_publication_profile(
        self, lecturer_id: UUID, data: PublicationProfileCreateRequest
    ) -> PublicationProfileResponse:
        raise NotImplementedError  # TODO

    def update_publication_profile(
        self,
        lecturer_id: UUID,
        publication_profile_id: int,
        data: PublicationProfileUpdateRequest,
    ) -> PublicationProfileResponse:
        raise NotImplementedError  # TODO

    def delete_publication_profile(self, lecturer_id: UUID, publication_profile_id: int) -> None:
        raise NotImplementedError  # TODO
