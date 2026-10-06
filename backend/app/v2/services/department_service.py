from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.department_dao import DepartmentDAO
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentListQuery,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.v2.models.department import Department
from app.v2.services.db_errors import is_unique_violation


class DepartmentService:
    def __init__(self, department_dao: DepartmentDAO) -> None:
        self.department_dao = department_dao

    def list_departments(self, query: DepartmentListQuery) -> PageResponse[DepartmentResponse]:
        items, total = self.department_dao.find_page(
            is_active=query.is_active, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[DepartmentResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_department(self, data: DepartmentCreateRequest) -> DepartmentResponse:
        if self.department_dao.get_by_code(data.code) is not None:
            raise ConflictError("Department code already used")
        try:
            department = self.department_dao.add(Department(**data.model_dump()))
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Department code already used") from exc
            raise
        return DepartmentResponse.model_validate(department)

    def update_department(
        self, department_id: int, data: DepartmentUpdateRequest
    ) -> DepartmentResponse:
        department = self.department_dao.get_by_id(department_id)
        if department is None:
            raise NotFoundError("Department not found")

        values = data.model_dump(exclude_unset=True)
        code = values.get("code")
        if (
            code is not None
            and code != department.code
            and self.department_dao.get_by_code(code) is not None
        ):
            raise ConflictError("Department code already used")
        try:
            department = self.department_dao.update(department, values)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Department code already used") from exc
            raise
        return DepartmentResponse.model_validate(department)
