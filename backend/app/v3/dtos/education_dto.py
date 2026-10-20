from typing import Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.v3.dtos.base import RequestDTO, ResponseDTO

_TEXT_FIELDS = ("degree", "field", "institution", "country", "graduation_year")


class _EducationFields(RequestDTO):
    degree: str | None = Field(default=None, max_length=100, examples=["Ph.D."])
    field: str | None = Field(default=None, max_length=255)
    institution: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    graduation_year: str | None = Field(default=None, max_length=10, examples=["2555"])

    @field_validator(*_TEXT_FIELDS)
    @classmethod
    def blank_is_null(cls, value: str | None) -> str | None:
        return value or None


class EducationCreateRequest(_EducationFields):
    @model_validator(mode="after")
    def require_some_content(self) -> Self:
        if all(getattr(self, name) is None for name in _TEXT_FIELDS):
            raise ValueError(f"At least one of {', '.join(_TEXT_FIELDS)} is required")
        return self


class EducationUpdateRequest(_EducationFields):
    @model_validator(mode="after")
    def require_some_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        return self


class EducationResponse(ResponseDTO):
    education_id: int
    lecturer_id: UUID
    degree: str | None
    field: str | None
    institution: str | None
    country: str | None
    graduation_year: str | None
