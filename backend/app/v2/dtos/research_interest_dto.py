from typing import Annotated

from pydantic import Field, field_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


class ResearchInterestCreateRequest(RequestDTO):
    name: str = Field(min_length=1, max_length=255, examples=["Machine Learning"])


class ResearchInterestUpdateRequest(RequestDTO):
    name: str = Field(min_length=1, max_length=255)


class ResearchInterestListQuery(PageQuery):
    q: str | None = Field(default=None, max_length=100)


class ResearchInterestResponse(ResponseDTO):
    research_interest_id: int
    name: str


class LecturerResearchInterestsReplaceRequest(RequestDTO):
    """PUT body: the lecturer's complete set of research interests (replaces the old set)."""

    research_interest_ids: list[Annotated[int, Field(strict=True, ge=1, le=32767)]]

    @field_validator("research_interest_ids")
    @classmethod
    def ids_must_be_unique(cls, values: list[int]) -> list[int]:
        if len(values) != len(set(values)):
            raise ValueError("research_interest_ids must not contain duplicates")
        return values
