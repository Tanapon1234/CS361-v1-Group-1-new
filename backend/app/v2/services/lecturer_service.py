"""Lecturer business logic. One method per endpoint; fill in the TODOs.

Tips: raise `NotFoundError` / `ConflictError` / `BadRequestError` from app.core.exceptions
(never HTTPException), and return DTOs, e.g. `LecturerResponse.model_validate(lecturer)`.
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.v2.daos.department_dao import DepartmentDAO
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
    def __init__(self, lecturer_dao: LecturerDAO, department_dao: DepartmentDAO) -> None:
        self.lecturer_dao = lecturer_dao
        self.department_dao = department_dao

    def create_lecturer(self, data: LecturerCreateRequest) -> LecturerResponse:
        if self.lecturer_dao.get_by_email(data.email) is not None:
            raise ConflictError("Email already used")
        self._check_department_and_account(data.department_id, data.cognito_sub)

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
            department_id=query.department_id,
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
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")

        values = data.model_dump(exclude_unset=True)
        if not values:
            return LecturerResponse.model_validate(lecturer)

        email = values.get("email")
        if email is not None and email != lecturer.email:
            duplicate = self.lecturer_dao.get_by_email(email)
            if duplicate is not None:
                raise ConflictError("Email already used")

        cognito_sub = values.get("cognito_sub")
        self._check_department_and_account(
            values.get("department_id"),
            cognito_sub if cognito_sub != lecturer.cognito_sub else None,
        )

        try:
            updated = self.lecturer_dao.update(lecturer, values)
        except IntegrityError as exc:
            if email is not None and _is_unique_violation(exc):
                raise ConflictError("Email already used") from exc
            raise

        return LecturerResponse.model_validate(updated)

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

    def _check_department_and_account(
        self, department_id: int | None, cognito_sub: str | None
    ) -> None:
        if department_id is not None and self.department_dao.get_by_id(department_id) is None:
            raise BadRequestError("Department not found")
        if cognito_sub is not None and self.lecturer_dao.get_by_cognito_sub(cognito_sub):
            raise ConflictError("cognito_sub is already linked to another lecturer")
