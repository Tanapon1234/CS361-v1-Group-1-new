"""Request validation for creating lecturer education records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

LECTURER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
EDUCATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
EDUCATION_FIELDS = {
    "degree",
    "field_of_study",
    "institution",
    "country",
    "graduation_year",
    "display_order",
}
CONTENT_FIELDS = ("degree", "field_of_study", "institution", "country", "graduation_year")
TEXT_FIELDS = ("degree", "field_of_study", "institution", "country")


class EducationValidationError(ValueError):
    """Invalid lecturer id or create-education payload."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class CreateEducationDTO:
    degree: str | None
    field_of_study: str | None
    institution: str | None
    country: str | None
    graduation_year: int | None
    display_order: int | None


@dataclass(frozen=True)
class PatchEducationDTO:
    degree: str | None
    field_of_study: str | None
    institution: str | None
    country: str | None
    graduation_year: int | None
    display_order: int | None
    provided_fields: frozenset[str]


def validate_lecturer_id(value: Any) -> str:
    if not isinstance(value, str):
        raise EducationValidationError("lecturerId", "lecturerId must be a valid identifier")
    lecturer_id = value.strip()
    if not LECTURER_ID_PATTERN.fullmatch(lecturer_id):
        raise EducationValidationError("lecturerId", "lecturerId must be a valid identifier")
    return lecturer_id


def validate_education_id(value: Any) -> str:
    if not isinstance(value, str):
        raise EducationValidationError("educationId", "educationId must be a valid identifier")
    education_id = value.strip()
    if not EDUCATION_ID_PATTERN.fullmatch(education_id):
        raise EducationValidationError("educationId", "educationId must be a valid identifier")
    return education_id


def parse_create_education(payload: Any) -> CreateEducationDTO:
    if not isinstance(payload, dict):
        raise EducationValidationError("body", "request body must be a JSON object")

    unknown_fields = set(payload) - EDUCATION_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise EducationValidationError(field, f"unknown field: {field}")

    values: dict[str, Any] = {}
    for field in TEXT_FIELDS:
        value = payload.get(field)
        if value is not None and not isinstance(value, str):
            raise EducationValidationError(field, f"{field} must be a string or null")
        values[field] = value.strip() or None if isinstance(value, str) else None

    graduation_year = payload.get("graduation_year")
    if graduation_year is not None and (
        isinstance(graduation_year, bool)
        or not isinstance(graduation_year, int)
        or not 1 <= graduation_year <= 9999
    ):
        raise EducationValidationError(
            "graduation_year", "graduation_year must be an integer from 1 to 9999"
        )

    display_order = payload.get("display_order")
    if "display_order" in payload and (
        isinstance(display_order, bool)
        or not isinstance(display_order, int)
        or display_order < 0
    ):
        raise EducationValidationError(
            "display_order", "display_order must be a non-negative integer"
        )

    values["graduation_year"] = graduation_year
    values["display_order"] = display_order
    if not any(values.get(field) is not None for field in CONTENT_FIELDS):
        raise EducationValidationError(
            "body",
            "at least one of degree, field_of_study, institution, country, or graduation_year is required",
        )

    return CreateEducationDTO(**values)


def parse_patch_education(payload: Any) -> PatchEducationDTO:
    if not isinstance(payload, dict):
        raise EducationValidationError("body", "request body must be a JSON object")
    if not payload:
        raise EducationValidationError("body", "at least one field must be provided")

    unknown_fields = set(payload) - EDUCATION_FIELDS
    if unknown_fields:
        field = sorted(unknown_fields)[0]
        raise EducationValidationError(field, f"unknown field: {field}")

    values: dict[str, Any] = {}
    for field in TEXT_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if value is not None and not isinstance(value, str):
            raise EducationValidationError(field, f"{field} must be a string or null")
        values[field] = value.strip() or None if isinstance(value, str) else None

    if "graduation_year" in payload:
        graduation_year = payload["graduation_year"]
        if graduation_year is not None and (
            isinstance(graduation_year, bool)
            or not isinstance(graduation_year, int)
            or not 1 <= graduation_year <= 9999
        ):
            raise EducationValidationError(
                "graduation_year", "graduation_year must be an integer from 1 to 9999 or null"
            )
        values["graduation_year"] = graduation_year

    if "display_order" in payload:
        display_order = payload["display_order"]
        if (
            isinstance(display_order, bool)
            or not isinstance(display_order, int)
            or display_order < 0
        ):
            raise EducationValidationError(
                "display_order", "display_order must be a non-negative integer"
            )
        values["display_order"] = display_order

    return PatchEducationDTO(
        degree=values.get("degree"),
        field_of_study=values.get("field_of_study"),
        institution=values.get("institution"),
        country=values.get("country"),
        graduation_year=values.get("graduation_year"),
        display_order=values.get("display_order"),
        provided_fields=frozenset(payload),
    )
