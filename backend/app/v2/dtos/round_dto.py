from datetime import date, datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.v2.dtos.base import QueryDTO, RequestDTO, ResponseDTO
from app.v2.dtos.common import Number, PageQuery
from app.v2.models.enums import SubmissionStatus


class RoundFields(RequestDTO):
    rubric_version_id: int = Field(ge=1, le=32767)
    name_th: str = Field(min_length=1, max_length=100, examples=["รอบ 1/2568"])
    period_start: date
    period_end: date
    salary_effective_on: date
    academic_year: int = Field(ge=2400, le=2800, examples=[2568])
    semester: int | None = Field(default=None, ge=1, le=3)
    submit_due_at: datetime | None = None
    is_open: bool = False

    @model_validator(mode="after")
    def period_is_valid(self) -> Self:
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        return self


class RoundCreateRequest(RoundFields):
    pass


class RoundUpdateRequest(RequestDTO):
    """Only sent fields change; open/close a round with `{"is_open": true|false}`."""

    rubric_version_id: int | None = Field(default=None, ge=1, le=32767)
    name_th: str | None = Field(default=None, min_length=1, max_length=100)
    period_start: date | None = None
    period_end: date | None = None
    salary_effective_on: date | None = None
    academic_year: int | None = Field(default=None, ge=2400, le=2800)
    semester: int | None = Field(default=None, ge=1, le=3)
    submit_due_at: datetime | None = None
    is_open: bool | None = None

    @field_validator(
        "rubric_version_id",
        "name_th",
        "period_start",
        "period_end",
        "salary_effective_on",
        "academic_year",
        "is_open",
    )
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class RoundListQuery(PageQuery):
    is_open: bool | None = None


class RoundResponse(ResponseDTO):
    id: int
    rubric_version_id: int
    name_th: str
    period_start: date
    period_end: date
    salary_effective_on: date
    academic_year: int
    semester: int | None
    submit_due_at: datetime | None
    is_open: bool


class RoundSubmissionsQuery(PageQuery):
    department_id: int | None = Field(default=None, ge=1, le=32767)
    status: SubmissionStatus | None = None


class RoundReportQuery(QueryDTO):
    department_id: int | None = Field(default=None, ge=1, le=32767)


class RoundReportRow(BaseModel):
    submission_id: UUID
    lecturer_id: UUID
    name_th: str
    department_id: int
    status: SubmissionStatus
    teaching_credits: Number
    raw_total: Number
    capped_total: Number
    meets_min_teaching_credits: bool
    meets_min_required: bool


class RoundReportSummary(BaseModel):
    submissions: int
    by_status: dict[SubmissionStatus, int]
    meeting_min_required: int
    average_capped_total: Number


class RoundReportResponse(BaseModel):
    round: RoundResponse
    min_required: Number
    min_teaching_credits: Number
    summary: RoundReportSummary
    rows: list[RoundReportRow]
