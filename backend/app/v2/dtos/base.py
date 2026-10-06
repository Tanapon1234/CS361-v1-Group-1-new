"""Base classes for DTOs (Data Transfer Objects): the API's public request/response shapes.

DTOs are deliberately separate from table models so the API contract can change
without touching the database, and so internal columns never leak to clients.
"""

from pydantic import BaseModel, ConfigDict


class RequestDTO(BaseModel):
    """JSON request bodies. Unknown fields are rejected to catch client typos early."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class QueryDTO(BaseModel):
    """Query-string parameters, used as `Annotated[SomeQuery, Query()]` in controllers."""

    model_config = ConfigDict(str_strip_whitespace=True)


class ResponseDTO(BaseModel):
    """Response bodies. Services build them from entities with `Dto.model_validate(entity)`."""

    model_config = ConfigDict(from_attributes=True)
