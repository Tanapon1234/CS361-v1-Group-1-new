from fastapi import APIRouter, status

from app.v2.controllers.params import LecturerId, PositionId
from app.v2.dependencies import PositionServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.position_dto import (
    PositionCreateRequest,
    PositionResponse,
    PositionUpdateRequest,
)

router = APIRouter(prefix="/lecturers/{lecturer_id}/positions", tags=["positions"])


@router.get("")
def list_positions(
    lecturer_id: LecturerId, service: PositionServiceDep
) -> ListResponse[PositionResponse]:
    """Every term the lecturer has held, newest first."""
    return service.list_positions(lecturer_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_position(
    lecturer_id: LecturerId, data: PositionCreateRequest, service: PositionServiceDep
) -> PositionResponse:
    """Appoint the lecturer to a position."""
    return service.create_position(lecturer_id, data)


@router.patch("/{position_id}")
def update_position(
    lecturer_id: LecturerId,
    position_id: PositionId,
    data: PositionUpdateRequest,
    service: PositionServiceDep,
) -> PositionResponse:
    """Usually to end the term: `{"end_date": "2026-09-30"}`."""
    return service.update_position(lecturer_id, position_id, data)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    lecturer_id: LecturerId, position_id: PositionId, service: PositionServiceDep
) -> None:
    """Only for a position recorded by mistake; end a real term with PATCH instead."""
    service.delete_position(lecturer_id, position_id)
