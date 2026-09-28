"""Shared list envelopes. Every collection response is `{"items": [...], "meta": {...}}`."""

from pydantic import BaseModel, Field

from app.v2.dtos.base import QueryDTO


class PageQuery(QueryDTO):
    """Offset pagination for unbounded collections."""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class PageResponse[T](BaseModel):
    """A page of an unbounded collection (lecturers, publications, master lists)."""

    items: list[T]
    meta: PageMeta


class ListMeta(BaseModel):
    count: int


class ListResponse[T](BaseModel):
    """A small, bounded sub-collection of one lecturer (educations, profiles, interests).

    Same envelope as the existing V2 master-data API.
    """

    items: list[T]
    meta: ListMeta
