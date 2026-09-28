from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


class ResearchInterestCreateRequest(RequestDTO):
    name: str = Field(min_length=1, max_length=255, examples=["Machine Learning"])


class ResearchInterestUpdateRequest(RequestDTO):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class ResearchInterestListQuery(PageQuery):
    q: str | None = Field(default=None, max_length=100)


class ResearchInterestResponse(ResponseDTO):
    research_interest_id: int
    name: str


class LecturerResearchInterestsReplaceRequest(RequestDTO):
    """PUT body: the lecturer's complete set of research interests (replaces the old set)."""

    research_interest_ids: list[int]
