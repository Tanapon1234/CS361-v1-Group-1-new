"""`GET /lecturers/{lecturer_id}/work`: one lecturer's work, filtered by year and category."""

from uuid import UUID

from pydantic import Field

from app.v2.models.enums import SubmissionStatus
from app.v3.dtos.base import QueryDTO, ResponseDTO
from app.v3.dtos.common import Number


class LecturerWorkQuery(QueryDTO):
    academic_year: int | None = Field(
        default=None, ge=2400, le=2800, description="Buddhist Era year, e.g. 2567"
    )
    category: str | None = Field(
        default=None, min_length=1, max_length=5, description="rubric_category.code, e.g. 2"
    )


class LecturerWorkFilters(ResponseDTO):
    """The filters that produced this result, so a client can describe an empty one."""

    academic_year: int | None
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


class WorkCategoryGroup(ResponseDTO):
    code: str
    name_th: str
    entries: list[WorkEntryResponse]


class WorkPublicationResponse(ResponseDTO):
    publication_id: int
    title: str
    publication_year: int | None
    academic_year: int | None = Field(description="publication_year converted to B.E.")
    venue: str | None
    doi: str | None
    author_order: int | None


class LecturerWorkResponse(ResponseDTO):
    lecturer_id: UUID
    lecturer_name_th: str
    filters: LecturerWorkFilters
    categories: list[WorkCategoryGroup]
    publications: list[WorkPublicationResponse]
    total: int = Field(description="Entries plus publications in this result")
    available_years: list[int] = Field(
        description="Every B.E. year this lecturer has any work in, newest first"
    )
