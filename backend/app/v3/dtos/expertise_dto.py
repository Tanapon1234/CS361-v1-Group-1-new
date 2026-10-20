from typing import Annotated

from pydantic import Field, field_validator

from app.v3.dtos.base import RequestDTO, ResponseDTO
from app.v3.dtos.common import PageQuery


class ExpertiseCreateRequest(RequestDTO):
    description: str = Field(min_length=1, examples=["Cloud Computing"])


class ExpertiseUpdateRequest(RequestDTO):
    description: str | None = Field(default=None, min_length=1)


class ExpertiseListQuery(PageQuery):
    q: str | None = Field(default=None, max_length=100)


class ExpertiseResponse(ResponseDTO):
    expertise_id: int
    description: str


class LecturerExpertiseReplaceRequest(RequestDTO):
    """PUT body: the lecturer's complete set of expertise (replaces the old set)."""

    expertise_ids: list[Annotated[int, Field(ge=1, le=32767)]]

    @field_validator("expertise_ids")
    @classmethod
    def no_duplicates(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("expertise_ids must not contain duplicates")
        return value
