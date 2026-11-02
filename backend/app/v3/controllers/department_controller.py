from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v3.controllers.params import DepartmentId
from app.v3.dependencies import CurrentActorDep, DepartmentServiceDep
from app.v3.dtos.common import PageResponse
from app.v3.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentListQuery,
    DepartmentReportQuery,
    DepartmentReportResponse,
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


@router.get("/{department_id}/report")
def get_department_report(
    department_id: DepartmentId,
    query: Annotated[DepartmentReportQuery, Query()],
    actor: CurrentActorDep,
    service: DepartmentServiceDep,
) -> DepartmentReportResponse:
    """Every lecturer's category totals in the department across a year range, plus
    lecturers with no submitted data yet (V4 FR7/FR8)."""
    return service.get_report(department_id, actor, query)
