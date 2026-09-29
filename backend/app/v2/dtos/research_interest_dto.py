from typing import Literal

from pydantic import BaseModel, Field

from app.v2.dtos.base import RequestDTO, ResponseDTO


class ResearchInterestCreateRequest(RequestDTO):
    name: str = Field(min_length=1, max_length=255, examples=["Machine Learning"])


class ResearchInterestUpdateRequest(RequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class ResearchInterestListQuery(RequestDTO):
    search: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    sort_order: Literal["asc", "desc"] = "asc"


class ResearchInterestResponse(ResponseDTO):
    research_interest_id: int
    name: str


class ResearchInterestPagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ResearchInterestListResponse(BaseModel):
    data: list[ResearchInterestResponse]
    pagination: ResearchInterestPagination


class LecturerResearchInterestsReplaceRequest(RequestDTO):
    """PUT body: the lecturer's complete set of research interests (replaces the old set)."""

    research_interest_ids: list[int]
