"""HTTP controller for lecturer education collection endpoints."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import re
from typing import Any

from .dao import DataApiEducationDao, LecturerNotFoundError
from .dto import EducationValidationError
from .service import LecturerEducationService

LOGGER = logging.getLogger(__name__)
EDUCATION_PATH_PATTERN = re.compile(r"^/api/v2/lecturers/([^/]+)/educations/?$")


def _json_response(
    status: int,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if headers:
        response_headers.update(headers)
    return {
        "statusCode": status,
        "headers": response_headers,
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
        "isBase64Encoded": False,
    }


def _method(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    return str(http.get("method") or event.get("httpMethod") or "GET").upper()


def _path(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    path = event.get("rawPath") or http.get("path") or event.get("path") or "/"
    return str(path).rstrip("/") or "/"


def _lecturer_id(event: dict[str, Any], path: str) -> str | None:
    params = event.get("pathParameters") or {}
    if isinstance(params, dict) and params.get("lecturerId") is not None:
        return params["lecturerId"]
    match = EDUCATION_PATH_PATTERN.fullmatch(path)
    return match.group(1) if match else None


def _request_body(event: dict[str, Any]) -> Any:
    body = event.get("body")
    if event.get("isBase64Encoded"):
        if body is not None and not isinstance(body, str):
            raise EducationValidationError("body", "request body must be valid UTF-8 JSON")
        try:
            body = base64.b64decode(body or "", validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise EducationValidationError("body", "request body must be valid UTF-8 JSON") from exc
    try:
        return json.loads(body) if isinstance(body, str) else body
    except json.JSONDecodeError as exc:
        raise EducationValidationError("body", "request body must be valid JSON") from exc


def _default_service() -> LecturerEducationService:
    return LecturerEducationService(
        DataApiEducationDao(
            resource_arn=os.environ["DB_CLUSTER_ARN"],
            secret_arn=os.environ["DB_SECRET_ARN"],
            database=os.environ["DB_NAME"],
        )
    )


def handle_request(
    event: dict[str, Any],
    service: LecturerEducationService | None = None,
) -> dict[str, Any]:
    event = event or {}
    path = _path(event)
    if EDUCATION_PATH_PATTERN.fullmatch(path) is None:
        return _json_response(404, {"error": {"code": "NOT_FOUND", "message": "Route not found"}})

    method = _method(event)
    if method not in {"GET", "POST"}:
        return _json_response(
            405,
            {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}},
            {"Allow": "GET, POST"},
        )

    try:
        lecturer_id = _lecturer_id(event, path)
        active_service = service if service is not None else _default_service()
        if method == "GET":
            items = active_service.list_for_lecturer(lecturer_id)
            return _json_response(
                200,
                {"items": items, "meta": {"count": len(items)}},
            )

        result = active_service.create(lecturer_id, _request_body(event))
        return _json_response(
            201,
            {"data": result},
            {"Location": f"{path.rstrip('/')}/{result['id']}"},
        )
    except EducationValidationError as exc:
        return _json_response(
            400,
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                    "details": {"field": exc.field},
                }
            },
        )
    except LecturerNotFoundError:
        return _json_response(
            404,
            {"error": {"code": "LECTURER_NOT_FOUND", "message": "Lecturer not found"}},
        )
    except Exception:
        LOGGER.exception("Failed to process lecturer education request")
        return _json_response(
            500,
            {"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
        )


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    return handle_request(event)
