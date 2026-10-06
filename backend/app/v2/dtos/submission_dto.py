from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.v2.dtos.base import QueryDTO, RequestDTO, ResponseDTO
from app.v2.dtos.common import Number, PageQuery
from app.v2.models.enums import (
    AcademicRank,
    ApprovalDecision,
    DataSource,
    SignerRole,
    SubmissionStatus,
)

# --- submission -------------------------------------------------------------------


class SubmissionCreateRequest(RequestDTO):
    """Creates the caller's own submission for a round."""

    round_id: int = Field(ge=1, le=32767)


class SubmissionListQuery(PageQuery):
    round_id: int | None = Field(default=None, ge=1, le=32767)
    lecturer_id: UUID | None = None
    status: SubmissionStatus | None = None


class SubmissionResponse(ResponseDTO):
    id: UUID
    round_id: int
    lecturer_id: UUID
    status: SubmissionStatus
    rank_snapshot: AcademicRank
    department_snapshot: int
    teaching_credits: Number
    raw_total: Number
    capped_total: Number
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- entries ----------------------------------------------------------------------


class EntryCreateRequest(RequestDTO):
    item_id: int = Field(ge=1, le=32767)
    title: str | None = Field(default=None, max_length=500)
    course_code: str | None = Field(default=None, max_length=15, examples=["CS222"])
    section_no: str | None = Field(default=None, max_length=10)
    student_count: int | None = Field(default=None, ge=0)
    data_source: DataSource = DataSource.MANUAL
    synced_at: datetime | None = None
    quantity: Decimal = Field(default=Decimal(1), gt=0, max_digits=8, decimal_places=2)
    participation_pct: Decimal = Field(
        default=Decimal(100), gt=0, le=100, max_digits=5, decimal_places=2
    )
    credits: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    details: dict[str, Any] | None = None
    note: str | None = Field(default=None, max_length=5000)
    sort_order: int = Field(default=0, ge=0, le=32767)


class EntryUpdateRequest(RequestDTO):
    """Only sent fields change. Send `If-Match: <ETag>` to avoid overwriting another tab."""

    item_id: int | None = Field(default=None, ge=1, le=32767)
    title: str | None = Field(default=None, max_length=500)
    course_code: str | None = Field(default=None, max_length=15)
    section_no: str | None = Field(default=None, max_length=10)
    student_count: int | None = Field(default=None, ge=0)
    data_source: DataSource | None = None
    synced_at: datetime | None = None
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    participation_pct: Decimal | None = Field(
        default=None, gt=0, le=100, max_digits=5, decimal_places=2
    )
    credits: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    details: dict[str, Any] | None = None
    note: str | None = Field(default=None, max_length=5000)
    sort_order: int | None = Field(default=None, ge=0, le=32767)

    @field_validator("item_id", "data_source", "quantity", "participation_pct", "sort_order")
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class EntryListQuery(QueryDTO):
    section: str | None = Field(default=None, max_length=10, description="Section code, e.g. 2.3.1")


class EntryResponse(ResponseDTO):
    id: UUID
    submission_id: UUID
    item_id: int
    title: str | None
    course_code: str | None
    section_no: str | None
    student_count: int | None
    data_source: DataSource
    synced_at: datetime | None
    quantity: Number
    participation_pct: Number
    # NULL while waiting for an assessor (ranged items) or for points-based items
    weight_applied: Number | None
    credits: Number | None
    # Always computed by the server
    score: Number
    details: dict[str, Any] | None
    note: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


def entry_etag(entry: EntryResponse) -> str:
    return f'"{entry.id}-{int(entry.updated_at.timestamp() * 1_000_000)}"'


class SubmissionDetailResponse(SubmissionResponse):
    entries: list[EntryResponse]


# --- summary (live) and totals (frozen) ------------------------------------------


class CategoryScore(BaseModel):
    category_id: int
    code: str
    name_th: str
    cap: Number
    raw_score: Number
    capped_score: Number


class SubmissionSummaryResponse(BaseModel):
    """Computed now from the entries (use while filling in the form)."""

    submission_id: UUID
    status: SubmissionStatus
    categories: list[CategoryScore]
    raw_total: Number
    capped_total: Number
    overall_cap: Number
    teaching_credits: Number
    min_teaching_credits: Number
    min_required: Number
    meets_min_teaching_credits: bool
    meets_min_required: bool
    # Entries of ranged items that no assessor has scored yet
    pending_assessments: int


class SubmissionTotalsResponse(BaseModel):
    """Frozen in submission_category_total when the submission is sent (use for review)."""

    submission_id: UUID
    status: SubmissionStatus
    submitted_at: datetime | None
    categories: list[CategoryScore]
    raw_total: Number
    capped_total: Number


# --- approvals --------------------------------------------------------------------


class ApprovalCreateRequest(RequestDTO):
    """`role` is never sent: the server takes it from the submission's status."""

    decision: ApprovalDecision
    comment: str | None = Field(default=None, max_length=2000)


class ApprovalResponse(ResponseDTO):
    id: UUID
    submission_id: UUID
    signer_id: UUID
    role: SignerRole
    decision: ApprovalDecision
    comment: str | None
    signed_at: datetime
