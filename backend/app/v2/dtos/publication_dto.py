from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


class PublicationCreateRequest(RequestDTO):
    title: str = Field(min_length=1)
    publication_year: int | None = None
    venue: str | None = None
    volume: str | None = Field(default=None, max_length=50)
    pages: str | None = Field(default=None, max_length=50)
    doi: str | None = Field(default=None, max_length=255)
    citation_text: str | None = None
    lecturer_ids: list[UUID] = Field(default_factory=list, description="Authors, in author order")


class PublicationUpdateRequest(RequestDTO):
    title: str | None = Field(default=None, min_length=1)
    publication_year: int | None = None
    venue: str | None = None
    volume: str | None = Field(default=None, max_length=50)
    pages: str | None = Field(default=None, max_length=50)
    doi: str | None = Field(default=None, max_length=255)
    citation_text: str | None = None
    lecturer_ids: list[UUID] | None = Field(default=None, description="Replaces all authors")


class PublicationListQuery(PageQuery):
    q: str | None = Field(default=None, max_length=200, description="Search title / venue / DOI")
    publication_year: int | None = None


class PublicationListItemResponse(ResponseDTO):
    publication_id: int
    title: str
    publication_year: int | None
    venue: str | None
    volume: str | None
    pages: str | None
    doi: str | None
    citation_text: str | None
    created_at: datetime | None


class PublicationResponse(PublicationListItemResponse):
    lecturer_ids: list[UUID] = Field(default_factory=list)


class LecturerPublicationResponse(PublicationListItemResponse):
    author_order: int | None
