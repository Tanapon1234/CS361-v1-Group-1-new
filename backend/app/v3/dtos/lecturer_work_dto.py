"""`GET /lecturers/{lecturer_id}/work`: one lecturer's work, filtered by a year range
and category, grouped by academic year then category."""

from uuid import UUID

from pydantic import Field

from app.v2.models.enums import SubmissionStatus, VerificationStatus
from app.v3.dtos.base import QueryDTO, ResponseDTO
from app.v3.dtos.common import Number


class LecturerWorkQuery(QueryDTO):
    academic_year_from: int | None = Field(
        default=None, ge=2400, le=2800, description="Buddhist Era year, e.g. 2566"
    )
    academic_year_to: int | None = Field(
        default=None, ge=2400, le=2800, description="Buddhist Era year, e.g. 2568"
    )
    category: str | None = Field(
        default=None, min_length=1, max_length=5, description="rubric_category.code, e.g. 2"
    )


class LecturerWorkFilters(ResponseDTO):
    """The filters that produced this result, so a client can describe an empty one."""

    academic_year_from: int | None
    academic_year_to: int | None
    category: str | None
    category_name_th: str | None


class WorkEntryResponse(ResponseDTO):
    entry_id: UUID
    submission_id: UUID
    submission_status: SubmissionStatus
    round_id: int
    round_name_th: str
    academic_year: int
    semester: int | None
    section_code: str
    section_name_th: str
    item_label_th: str
    title: str | None
    course_code: str | None
    quantity: Number
    score: Number
    evidence_count: int = Field(description="Supporting files attached to this entry")


class WorkCategoryGroup(ResponseDTO):
    code: str
    name_th: str
    entries: list[WorkEntryResponse]
    total_score: Number = Field(description="Sum of entries' score in this category, this year")


class WorkPublicationResponse(ResponseDTO):
    publication_id: int
    title: str
    publication_year: int | None
    academic_year: int | None = Field(description="publication_year converted to B.E.")
    venue: str | None
    doi: str | None
    author_order: int | None
    verification_status: VerificationStatus


class WorkYearGroup(ResponseDTO):
    academic_year: int
    categories: list[WorkCategoryGroup]
    publications: list[WorkPublicationResponse]
    total_score: Number = Field(description="Sum of every entry's score in this year")


class LecturerWorkResponse(ResponseDTO):
    lecturer_id: UUID
    lecturer_name_th: str
    filters: LecturerWorkFilters
    years: list[WorkYearGroup] = Field(description="Newest academic year first")
    total: int = Field(description="Entries plus publications in this result")
    available_years: list[int] = Field(
        description="Every B.E. year this lecturer has any work in, newest first"
    )
