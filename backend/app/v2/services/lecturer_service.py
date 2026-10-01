"""Lecturer business logic. One method per endpoint; fill in the TODOs.

Tips: raise `NotFoundError` / `ConflictError` / `BadRequestError` from app.core.exceptions
(never HTTPException), and return DTOs, e.g. `LecturerResponse.model_validate(lecturer)`.
"""

from uuid import UUID

from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import PageResponse
from app.v2.dtos.lecturer_dto import (
    LecturerCreateRequest,
    LecturerListQuery,
    LecturerResponse,
    LecturerUpdateRequest,
)


class LecturerService:
    def __init__(self, lecturer_dao: LecturerDAO) -> None:
        self.lecturer_dao = lecturer_dao

    def create_lecturer(self, data: LecturerCreateRequest) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def list_lecturers(self, query: LecturerListQuery) -> PageResponse[LecturerResponse]:
        raise NotImplementedError  # TODO

    def get_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def update_lecturer(self, lecturer_id: UUID, data: LecturerUpdateRequest) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def activate_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        raise NotImplementedError  # TODO: is_active = True

    def deactivate_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        raise NotImplementedError  # TODO: is_active = False
