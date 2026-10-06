from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import DepartmentId
from app.v2.dependencies import DepartmentServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentListQuery,
    DepartmentResponse,
    DepartmentUpdateRequest,
)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("")
def list_departments(
    query: Annotated[DepartmentListQuery, Query()], service: DepartmentServiceDep
) -> PageResponse[DepartmentResponse]:
    return service.list_departments(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreateRequest, service: DepartmentServiceDep
) -> DepartmentResponse:
    return service.create_department(data)


@router.patch("/{department_id}")
def update_department(
    department_id: DepartmentId, data: DepartmentUpdateRequest, service: DepartmentServiceDep
) -> DepartmentResponse:
    """Rename, or close with `{"is_active": false}`."""
    return service.update_department(department_id, data)
