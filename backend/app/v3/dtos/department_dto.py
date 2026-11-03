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
    rows: list[DepartmentReportCategoryRow]
    missing: list[DepartmentReportMissingRow]
