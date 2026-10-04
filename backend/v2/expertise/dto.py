"""Request and response data transfer objects for expertise endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ExpertiseValidationError(Exception):
    """Invalid create-expertise request data."""

    def __init__(self, field: str | None, message: str) -> None:
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class CreateExpertiseDTO:
    faculty_id: str
    value: str

    @classmethod
    def from_mapping(cls, payload: Any) -> CreateExpertiseDTO:
        if not isinstance(payload, dict):
            raise ExpertiseValidationError(None, "Request body must be a JSON object")

        if set(payload) != {"faculty_id", "value"}:
            raise ExpertiseValidationError(
                None,
                "Request body must contain only faculty_id and value",
            )

        faculty_id = payload["faculty_id"]
        if not isinstance(faculty_id, str) or not faculty_id.strip():
            raise ExpertiseValidationError(
                "faculty_id",
                "faculty_id must be a non-empty string",
            )

        value = payload["value"]
        if not isinstance(value, str) or not value.strip():
            raise ExpertiseValidationError(
                "value",
                "value must be a non-empty string",
            )

        return cls(faculty_id=faculty_id.strip(), value=value.strip())
