from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


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

    expertise_ids: list[int]
