from uuid import UUID

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.dtos.common import ListResponse
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
        raise NotImplementedError  # TODO

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
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

        profile = self.publication_profile_dao.get_by_id(publication_profile_id)
        if profile is None or profile.lecturer_id != lecturer_id:
            raise NotFoundError("Publication profile not found")

        self.publication_profile_dao.delete(profile)
