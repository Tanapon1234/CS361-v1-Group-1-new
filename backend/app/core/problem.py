from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ProblemDetail(BaseModel):
    """RFC 9457 (formerly RFC 7807) problem details: the body of every 4xx/5xx response.

    Served with `Content-Type: application/problem+json`.
    """

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    errors: list[FieldError] | None = None
