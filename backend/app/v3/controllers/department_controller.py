from typing import Annotated

from fastapi import APIRouter, Query, Response, status

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
    department_report_to_csv,
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


@router.get("/{department_id}/report", response_model=None)
def get_department_report(
    department_id: DepartmentId,
    query: Annotated[DepartmentReportQuery, Query()],
    actor: CurrentActorDep,
    service: DepartmentServiceDep,
) -> DepartmentReportResponse | Response:
    """Every lecturer's category totals in the department across a year range, plus
    lecturers with no submitted data yet (V4 FR7/FR8). `?format=csv` for a file staff
    can drop into the annual report (V4 TC2) instead of the JSON body."""
    report = service.get_report(department_id, actor, query)
    if query.format == "csv":
        filename = f"department-{department_id}-report.csv"
        return Response(
            content=department_report_to_csv(report),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return report
