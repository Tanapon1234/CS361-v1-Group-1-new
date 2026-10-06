from pydantic import Field, field_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery


class DepartmentCreateRequest(RequestDTO):
    code: str = Field(min_length=1, max_length=10, examples=["CS"])
    name_th: str = Field(min_length=1, max_length=150, examples=["วิทยาการคอมพิวเตอร์"])
    is_active: bool = True


class DepartmentUpdateRequest(RequestDTO):
    code: str | None = Field(default=None, min_length=1, max_length=10)
    name_th: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None

    @field_validator("code", "name_th", "is_active")
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class DepartmentListQuery(PageQuery):
    is_active: bool | None = None


class DepartmentResponse(ResponseDTO):
    id: int
    code: str
    name_th: str
    is_active: bool
