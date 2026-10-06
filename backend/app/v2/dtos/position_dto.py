from datetime import date
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.models.enums import PositionCode


class PositionCreateRequest(RequestDTO):
    position: PositionCode
    # Required for department-level positions (dept_*), must be empty for faculty-level ones
    department_id: int | None = Field(default=None, ge=1, le=32767)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class PositionUpdateRequest(RequestDTO):
    """Usually only `end_date`, to close a term. Send `end_date: null` to reopen it."""

    start_date: date | None = None
    end_date: date | None = None


class PositionResponse(ResponseDTO):
    id: UUID
    lecturer_id: UUID
    position: PositionCode
    department_id: int | None
    start_date: date
    end_date: date | None
