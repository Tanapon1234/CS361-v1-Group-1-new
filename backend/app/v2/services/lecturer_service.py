"""Lecturer business logic. One method per endpoint; fill in the TODOs.

Tips: raise `NotFoundError` / `ConflictError` / `BadRequestError` from app.core.exceptions
(never HTTPException), and return DTOs, e.g. `LecturerResponse.model_validate(lecturer)`.
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.lecturer_dto import (
    LecturerCreateRequest,
    LecturerListQuery,
    LecturerResponse,
    LecturerUpdateRequest,
)
from app.v2.models.lecturer import Lecturer


def _is_unique_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)
    if sqlstate == "23505":
        return True
    return "unique constraint failed" in str(exc.orig).lower()


class LecturerService:
    def __init__(self, lecturer_dao: LecturerDAO) -> None:
        self.lecturer_dao = lecturer_dao

    def create_lecturer(self, data: LecturerCreateRequest) -> LecturerResponse:
        if self.lecturer_dao.get_by_email(data.email) is not None:
            raise ConflictError("Email already used")

        try:
            lecturer = self.lecturer_dao.add(Lecturer(**data.model_dump()))
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                raise ConflictError("Email already used") from exc
            raise

        return LecturerResponse.model_validate(lecturer)

    def list_lecturers(self, query: LecturerListQuery) -> PageResponse[LecturerResponse]:
        items, total = self.lecturer_dao.find_page(
            q=query.q,
            is_active=query.is_active,
            limit=query.limit,
            offset=query.offset,
        )
        return PageResponse(
            items=[LecturerResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def get_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        return LecturerResponse.model_validate(lecturer)

    def update_lecturer(self, lecturer_id: UUID, data: LecturerUpdateRequest) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def activate_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        if lecturer.is_active:
            return LecturerResponse.model_validate(lecturer)

        updated = self.lecturer_dao.update(lecturer, {"is_active": True})
        return LecturerResponse.model_validate(updated)

    def deactivate_lecturer(self, lecturer_id: UUID) -> LecturerResponse:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        if not lecturer.is_active:
            return LecturerResponse.model_validate(lecturer)

        updated = self.lecturer_dao.update(lecturer, {"is_active": False})
        return LecturerResponse.model_validate(updated)
