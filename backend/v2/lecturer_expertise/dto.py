"""Request data transfer objects for lecturer-expertise mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class LecturerExpertiseValidationError(Exception):
    """Invalid lecturer-expertise request data."""

    def __init__(self, field: str | None, message: str) -> None:
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class ReplaceLecturerExpertiseDTO:
    expertise_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, payload: Any) -> ReplaceLecturerExpertiseDTO:
        if not isinstance(payload, dict):
            raise LecturerExpertiseValidationError(
                None,
                "Request body must be a JSON object",
            )

        if set(payload) != {"expertiseIds"}:
            raise LecturerExpertiseValidationError(
                None,
                "Request body must contain only expertiseIds",
            )

        expertise_ids = payload["expertiseIds"]
        if not isinstance(expertise_ids, list):
            raise LecturerExpertiseValidationError(
                "expertiseIds",
                "expertiseIds must be an array of non-empty strings",
            )

        normalized_ids: list[str] = []
        for expertise_id in expertise_ids:
            if not isinstance(expertise_id, str) or not expertise_id.strip():
                raise LecturerExpertiseValidationError(
                    "expertiseIds",
                    "expertiseIds must contain only non-empty strings",
                )
            normalized_ids.append(expertise_id.strip())

        if len(normalized_ids) != len(set(normalized_ids)):
            raise LecturerExpertiseValidationError(
                "expertiseIds",
                "expertiseIds must not contain duplicates",
            )

        return cls(expertise_ids=tuple(normalized_ids))
