"""Expertise assigned to one lecturer."""

from fastapi import APIRouter, status

from app.v2.controllers.params import ExpertiseId, LecturerId
from app.v2.dependencies import ExpertiseServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.expertise_dto import ExpertiseResponse, LecturerExpertiseReplaceRequest

router = APIRouter(prefix="/lecturers/{lecturer_id}/expertise", tags=["expertise"])


@router.get("")
def list_lecturer_expertise(
    lecturer_id: LecturerId, service: ExpertiseServiceDep
) -> ListResponse[ExpertiseResponse]:
    return service.list_lecturer_expertise(lecturer_id)


@router.put("")
def replace_lecturer_expertise(
    lecturer_id: LecturerId, data: LecturerExpertiseReplaceRequest, service: ExpertiseServiceDep
) -> ListResponse[ExpertiseResponse]:
    """Replace the lecturer's whole set of expertise."""
    return service.replace_lecturer_expertise(lecturer_id, data)


@router.delete("/{expertise_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lecturer_expertise(
    lecturer_id: LecturerId, expertise_id: ExpertiseId, service: ExpertiseServiceDep
) -> None:
    service.remove_lecturer_expertise(lecturer_id, expertise_id)
