import csv
import io
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.v3.dtos.base import QueryDTO, RequestDTO, ResponseDTO
from app.v3.dtos.common import Number, PageQuery


class DepartmentCreateRequest(RequestDTO):
    code: str = Field(min_length=1, max_length=10, examples=["CS"])
    name_th: str = Field(min_length=1, max_length=150, examples=["วิทยาการคอมพิวเตอร์"])
    is_active: bool = True


class DepartmentUpdateRequest(RequestDTO):
    code: str | None = Field(default=None, min_length=1, max_length=10)
    name_th: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None

    @field_validator("code", "name_th", "is_active")
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class DepartmentListQuery(PageQuery):
    is_active: bool | None = None


class DepartmentResponse(ResponseDTO):
    id: int
    code: str
    name_th: str
    is_active: bool


class DepartmentReportQuery(QueryDTO):
    academic_year_from: int = Field(ge=2400, le=2800, examples=[2566])
    academic_year_to: int = Field(ge=2400, le=2800, examples=[2568])
    category_code: str | None = Field(
        default=None, min_length=1, max_length=5, description="rubric_category.code, e.g. 2"
    )
    lecturer_id: UUID | None = None
    format: Literal["json", "csv"] = "json"


class DepartmentReportCategoryRow(BaseModel):
    """One lecturer's frozen category total (submission_category_total) for one year."""

    lecturer_id: UUID
    name_th: str
    academic_year: int
    category_code: str
    category_name_th: str
    raw_score: Number
    capped_score: Number


class DepartmentReportMissingRow(BaseModel):
    """An active lecturer of the department with no submitted data for this year."""

    lecturer_id: UUID
    name_th: str
    academic_year: int


class DepartmentReportResponse(BaseModel):
    department: DepartmentResponse
    academic_year_from: int
    academic_year_to: int
    category_code: str | None = None
    lecturer_id: UUID | None = None
    rows: list[DepartmentReportCategoryRow]
    missing: list[DepartmentReportMissingRow]


def department_report_to_csv(report: DepartmentReportResponse) -> str:
    """`rows` and `missing` flattened into one table, for `?format=csv` (V4 TC2:
    something staff can drop straight into the annual report)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "lecturer_name_th",
            "academic_year",
            "category_code",
            "category_name_th",
            "raw_score",
            "capped_score",
            "status",
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.name_th,
                row.academic_year,
                row.category_code,
                row.category_name_th,
                row.raw_score,
                row.capped_score,
                "submitted",
            ]
        )
    for row in report.missing:
        writer.writerow([row.name_th, row.academic_year, "", "", "", "", "missing"])
    return buffer.getvalue()
