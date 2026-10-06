from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


class LecturerCreateRequest(RequestDTO):
    name_th: str = Field(min_length=1, max_length=255)
    name_en: str | None = Field(default=None, max_length=255)
    rank: str | None = Field(default=None, max_length=100)
    department_id: int | None = Field(default=None, ge=1, le=32767)
    # Cognito `sub` of the lecturer's account. Write-only: never returned.
    cognito_sub: str | None = Field(default=None, min_length=1, max_length=64)
    office: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    phone_extension: str | None = Field(default=None, max_length=50)
    email: EmailStr


class LecturerUpdateRequest(RequestDTO):
    """PATCH body: only fields that are sent get updated (`model_dump(exclude_unset=True)`)."""

    name_th: str | None = Field(default=None, min_length=1, max_length=255)
    name_en: str | None = Field(default=None, max_length=255)
    rank: str | None = Field(default=None, max_length=100)
    department_id: int | None = Field(default=None, ge=1, le=32767)
    # Cognito `sub` of the lecturer's account. Write-only: never returned.
    cognito_sub: str | None = Field(default=None, min_length=1, max_length=64)
    office: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    phone_extension: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None

    @field_validator("name_th", "email")
    @classmethod
    def required_fields_must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class LecturerListQuery(PageQuery):
    q: str | None = Field(default=None, max_length=100, description="Search name / email")
    is_active: bool | None = None
    department_id: int | None = Field(default=None, ge=1, le=32767)


class LecturerResponse(ResponseDTO):
    # cv_url is not exposed here; clients use GET /lecturers/{lecturer_id}/cv
    # cognito_sub is internal (auth mapping), never returned
    lecturer_id: UUID
    name_th: str
    name_en: str | None
    rank: str | None
    department_id: int | None
    profile_image_url: str | None
    office: str | None
    phone: str | None
    phone_extension: str | None
    email: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
