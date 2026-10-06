from uuid import UUID

from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import ListResponse
from app.v2.dtos.education_dto import (
    EducationCreateRequest,
    EducationResponse,
    EducationUpdateRequest,
)


class EducationService:
    def __init__(self, education_dao: EducationDAO, lecturer_dao: LecturerDAO) -> None:
        self.education_dao = education_dao
        self.lecturer_dao = lecturer_dao

    def list_educations(self, lecturer_id: UUID) -> ListResponse[EducationResponse]:
        raise NotImplementedError  # TODO

    def create_education(
        self, lecturer_id: UUID, data: EducationCreateRequest
    ) -> EducationResponse:
        raise NotImplementedError  # TODO

    def update_education(
        self, lecturer_id: UUID, education_id: int, data: EducationUpdateRequest
    ) -> EducationResponse:
        raise NotImplementedError  # TODO

    def delete_education(self, lecturer_id: UUID, education_id: int) -> None:
        raise NotImplementedError  # TODO
