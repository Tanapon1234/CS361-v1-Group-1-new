from fastapi import APIRouter, status

from app.v2.controllers.params import EducationId, LecturerId
from app.v2.dependencies import EducationServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.education_dto import (
    EducationCreateRequest,
    EducationResponse,
    EducationUpdateRequest,
)

router = APIRouter(prefix="/lecturers/{lecturer_id}/educations", tags=["educations"])


@router.get("")
def list_educations(
    lecturer_id: LecturerId, service: EducationServiceDep
) -> ListResponse[EducationResponse]:
    return service.list_educations(lecturer_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_education(
    lecturer_id: LecturerId, data: EducationCreateRequest, service: EducationServiceDep
) -> EducationResponse:
    return service.create_education(lecturer_id, data)


@router.patch("/{education_id}")
def update_education(
    lecturer_id: LecturerId,
    education_id: EducationId,
    data: EducationUpdateRequest,
    service: EducationServiceDep,
) -> EducationResponse:
    return service.update_education(lecturer_id, education_id, data)


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education(
    lecturer_id: LecturerId, education_id: EducationId, service: EducationServiceDep
) -> None:
    service.delete_education(lecturer_id, education_id)
