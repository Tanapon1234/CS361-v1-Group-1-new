from uuid import UUID

from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO


class EducationCreateRequest(RequestDTO):
    degree: str | None = Field(default=None, max_length=100, examples=["Ph.D."])
    field: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    graduation_year: str | None = Field(default=None, max_length=10, examples=["2555"])


class EducationUpdateRequest(RequestDTO):
    degree: str | None = Field(default=None, max_length=100)
    field: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    graduation_year: str | None = Field(default=None, max_length=10)


class EducationResponse(ResponseDTO):
    education_id: int
    lecturer_id: UUID
    degree: str | None
    field: str | None
    institution: str | None
    country: str | None
    graduation_year: str | None
