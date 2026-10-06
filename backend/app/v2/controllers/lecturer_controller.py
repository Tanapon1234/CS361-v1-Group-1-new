from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import LecturerId
from app.v2.dependencies import LecturerServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.lecturer_dto import (
    LecturerCreateRequest,
    LecturerListQuery,
    LecturerResponse,
    LecturerUpdateRequest,
)

router = APIRouter(prefix="/lecturers", tags=["lecturers"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_lecturer(data: LecturerCreateRequest, service: LecturerServiceDep) -> LecturerResponse:
    return service.create_lecturer(data)


@router.get("")
def list_lecturers(
    query: Annotated[LecturerListQuery, Query()], service: LecturerServiceDep
) -> PageResponse[LecturerResponse]:
    return service.list_lecturers(query)


@router.get("/{lecturer_id}")
def get_lecturer(lecturer_id: LecturerId, service: LecturerServiceDep) -> LecturerResponse:
    return service.get_lecturer(lecturer_id)


@router.patch("/{lecturer_id}")
def update_lecturer(
    lecturer_id: LecturerId, data: LecturerUpdateRequest, service: LecturerServiceDep
) -> LecturerResponse:
    return service.update_lecturer(lecturer_id, data)


@router.post("/{lecturer_id}/activate")
def activate_lecturer(lecturer_id: LecturerId, service: LecturerServiceDep) -> LecturerResponse:
    return service.activate_lecturer(lecturer_id)


@router.post("/{lecturer_id}/deactivate")
def deactivate_lecturer(lecturer_id: LecturerId, service: LecturerServiceDep) -> LecturerResponse:
    return service.deactivate_lecturer(lecturer_id)
