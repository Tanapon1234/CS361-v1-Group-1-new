from uuid import UUID

from app.core.exceptions import NotFoundError
from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.education_dto import (
    EducationCreateRequest,
    EducationResponse,
    EducationUpdateRequest,
)
from app.v2.models.education import Education


class EducationService:
    def __init__(self, education_dao: EducationDAO, lecturer_dao: LecturerDAO) -> None:
        self.education_dao = education_dao
        self.lecturer_dao = lecturer_dao

    def list_educations(self, lecturer_id: UUID) -> ListResponse[EducationResponse]:
        self._require_lecturer(lecturer_id)
        items = [
            EducationResponse.model_validate(education)
            for education in self.education_dao.list_by_lecturer(lecturer_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_education(
        self, lecturer_id: UUID, data: EducationCreateRequest
    ) -> EducationResponse:
        self._require_lecturer(lecturer_id)
        education = self.education_dao.add(Education(lecturer_id=lecturer_id, **data.model_dump()))
        return EducationResponse.model_validate(education)

    def update_education(
        self, lecturer_id: UUID, education_id: int, data: EducationUpdateRequest
    ) -> EducationResponse:
        education = self._require_education(lecturer_id, education_id)
        updated = self.education_dao.update(education, data.model_dump(exclude_unset=True))
        return EducationResponse.model_validate(updated)

    def delete_education(self, lecturer_id: UUID, education_id: int) -> None:
        self.education_dao.delete(self._require_education(lecturer_id, education_id))

    def _require_lecturer(self, lecturer_id: UUID) -> None:
        if self.lecturer_dao.get_by_id(lecturer_id) is None:
            raise NotFoundError("Lecturer not found")

    def _require_education(self, lecturer_id: UUID, education_id: int) -> Education:
        self._require_lecturer(lecturer_id)
        education = self.education_dao.get_by_id(education_id)
        # Another lecturer's row is reported as missing, not forbidden
        if education is None or education.lecturer_id != lecturer_id:
            raise NotFoundError("Education not found")
        return education
