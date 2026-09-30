from uuid import UUID

from pydantic import AnyHttpUrl, Field, TypeAdapter, ValidationError, field_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO

_HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)


class PublicationProfileCreateRequest(RequestDTO):
    provider: str = Field(min_length=1, max_length=100, examples=["Google Scholar"])
    url: str = Field(min_length=1, examples=["https://scholar.google.com/citations?user=..."])

    @field_validator("url")
    @classmethod
    def url_must_be_http_or_https(cls, value: str) -> str:
        try:
            _HTTP_URL_ADAPTER.validate_python(value)
        except ValidationError as exc:
            raise ValueError("url must be a valid HTTP or HTTPS URL") from exc
        return value


class PublicationProfileUpdateRequest(RequestDTO):
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1)


class PublicationProfileResponse(ResponseDTO):
    publication_profile_id: int
    lecturer_id: UUID
    provider: str
    url: str
