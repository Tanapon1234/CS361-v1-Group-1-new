"""Faculty id validation.

Allowed:  lowercase a-z, 0-9 and single ``-`` separators.
Rejected: empty, ``../``, ``/``, ``\\``, control characters, uppercase,
percent-encoded traversal, over-long ids, anything else.
"""

from __future__ import annotations

import re
from urllib.parse import unquote

FACULTY_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_FACULTY_ID_LENGTH = 64


class InvalidFacultyIdError(ValueError):
    """Raised when a faculty id fails validation -> HTTP 400."""

    def __init__(self, reason: str = "invalid_format") -> None:
        super().__init__(reason)
        self.reason = reason


def _has_control_characters(value: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


def validate_faculty_id(raw_id) -> str:
    """Return the validated faculty id or raise :class:`InvalidFacultyIdError`."""
    if raw_id is None or not isinstance(raw_id, str):
        raise InvalidFacultyIdError("missing_id")

    if raw_id == "" or raw_id.strip() == "":
        raise InvalidFacultyIdError("empty_id")

    if len(raw_id) > MAX_FACULTY_ID_LENGTH:
        raise InvalidFacultyIdError("too_long")

    if _has_control_characters(raw_id):
        raise InvalidFacultyIdError("control_character")

    # Defend against double-encoded traversal (%2e%2e%2f, %2f, %5c ...).
    # The decoded form must be identical to the raw form *and* still match.
    decoded = raw_id
    for _ in range(2):
        nxt = unquote(decoded)
        if nxt == decoded:
            break
        decoded = nxt

    if decoded != raw_id:
        raise InvalidFacultyIdError("encoded_input")

    for candidate in (raw_id, decoded):
        if _has_control_characters(candidate):
            raise InvalidFacultyIdError("control_character")
        if "/" in candidate or "\\" in candidate or ".." in candidate or "%" in candidate:
            raise InvalidFacultyIdError("path_traversal")
        if not FACULTY_ID_PATTERN.match(candidate):
            raise InvalidFacultyIdError("invalid_format")

    return raw_id
