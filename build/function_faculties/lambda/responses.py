"""HTTP response / error mapping for the Faculty API.

Public responses only ever contain a stable error ``code`` and a short,
non-sensitive ``message``.  Internal exception payloads are logged, never
returned to the caller.
"""

from __future__ import annotations

import json
from typing import Any, Dict

JSON_CONTENT_TYPE = "application/json; charset=utf-8"

# Stable, public error codes
INVALID_FACULTY_ID = "INVALID_FACULTY_ID"
FACULTY_NOT_FOUND = "FACULTY_NOT_FOUND"
ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"
METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
INTERNAL_ERROR = "INTERNAL_ERROR"

_PUBLIC_MESSAGES = {
    INVALID_FACULTY_ID: "Faculty id format is invalid.",
    FACULTY_NOT_FOUND: "Faculty not found.",
    ROUTE_NOT_FOUND: "Route not found.",
    METHOD_NOT_ALLOWED: "Method not allowed.",
    INTERNAL_ERROR: "Internal server error.",
}


def _base_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    headers = {
        "Content-Type": JSON_CONTENT_TYPE,
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if extra:
        headers.update(extra)
    return headers


def _envelope(status_code: int, body: Dict[str, Any],
              headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": _base_headers(headers),
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
        "isBase64Encoded": False,
    }


def ok(data: Any) -> Dict[str, Any]:
    """200 with the required ``{"data": ...}`` envelope."""
    return _envelope(200, {"data": data})


def error(status_code: int, code: str, message: str | None = None,
          headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    return _envelope(
        status_code,
        {"error": {"code": code, "message": message or _PUBLIC_MESSAGES.get(code, "Error.")}},
        headers,
    )


def bad_request(message: str | None = None) -> Dict[str, Any]:
    return error(400, INVALID_FACULTY_ID, message)


def not_found(code: str = FACULTY_NOT_FOUND) -> Dict[str, Any]:
    return error(404, code)


def method_not_allowed(allowed: str = "GET") -> Dict[str, Any]:
    return error(405, METHOD_NOT_ALLOWED, headers={"Allow": allowed})


def internal_error() -> Dict[str, Any]:
    return error(500, INTERNAL_ERROR)
