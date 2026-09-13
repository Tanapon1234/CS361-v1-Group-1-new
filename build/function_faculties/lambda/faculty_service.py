"""Faculty domain logic.

List   -> one GetObject on ``serving/faculties.json``
Detail -> one GetObject on ``serving/faculties/{id}.json``

The list is never assembled by looping over detail objects.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from s3_repository import (
    InvalidJsonError,
    ObjectAccessError,
    ObjectNotFoundError,
    S3Repository,
)
from validation import validate_faculty_id

logger = logging.getLogger(__name__)

LIST_KEY = "faculties.json"
DETAIL_KEY_TEMPLATE = "faculties/{faculty_id}.json"


class FacultyNotFoundError(Exception):
    """Detail object does not exist -> HTTP 404."""


class BackendDataError(Exception):
    """Missing list object, malformed JSON or S3 failure -> HTTP 500."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class FacultyService:
    def __init__(self, repository: S3Repository) -> None:
        self._repository = repository

    # ---------------------------------------------------------------- list
    def list_faculties(self) -> List[Any]:
        try:
            payload = self._repository.get_json(LIST_KEY)
        except ObjectNotFoundError as exc:
            # The directory object is required infrastructure, not user input.
            raise BackendDataError("list_object_missing") from exc
        except InvalidJsonError as exc:
            raise BackendDataError("list_invalid_json") from exc
        except ObjectAccessError as exc:
            raise BackendDataError("list_storage_error") from exc

        return _extract_list(payload)

    # -------------------------------------------------------------- detail
    def get_faculty(self, raw_faculty_id: str) -> Dict[str, Any]:
        faculty_id = validate_faculty_id(raw_faculty_id)
        key = DETAIL_KEY_TEMPLATE.format(faculty_id=faculty_id)

        try:
            payload = self._repository.get_json(key)
        except ObjectNotFoundError as exc:
            raise FacultyNotFoundError(faculty_id) from exc
        except InvalidJsonError as exc:
            raise BackendDataError("detail_invalid_json") from exc
        except ObjectAccessError as exc:
            raise BackendDataError("detail_storage_error") from exc

        return _extract_detail(payload, faculty_id)


def _extract_list(payload: Any) -> List[Any]:
    """Accept ``[...]``, ``{"data": [...]}`` or ``{"faculties": [...]}``."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for field in ("data", "faculties", "items"):
            if field in payload:
                value = payload[field]
                if isinstance(value, list):
                    return value
                if value is None:
                    return []
                raise BackendDataError("list_shape_invalid")
    raise BackendDataError("list_shape_invalid")


def _extract_detail(payload: Any, faculty_id: str) -> Dict[str, Any]:
    """Accept ``{...}`` or ``{"data": {...}}``; a null/absent object is a 404."""
    if isinstance(payload, dict) and set(payload.keys()) == {"data"}:
        payload = payload["data"]

    if payload is None:
        raise FacultyNotFoundError(faculty_id)
    if not isinstance(payload, dict):
        raise BackendDataError("detail_shape_invalid")
    if not payload:
        # Empty object is a valid (if sparse) faculty document.
        return {}
    return payload
