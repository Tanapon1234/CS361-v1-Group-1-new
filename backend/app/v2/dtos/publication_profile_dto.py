from uuid import UUID

from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO


class PublicationProfileCreateRequest(RequestDTO):
    provider: str = Field(min_length=1, max_length=100, examples=["Google Scholar"])
    url: str = Field(min_length=1, examples=["https://scholar.google.com/citations?user=..."])


class PublicationProfileUpdateRequest(RequestDTO):
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1)


class PublicationProfileResponse(ResponseDTO):
    publication_profile_id: int
    lecturer_id: UUID
    provider: str
    url: str
