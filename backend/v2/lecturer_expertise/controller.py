"""HTTP Lambda controller for lecturer-expertise mapping endpoints."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Any

from .dao import (
    DeferredLecturerExpertiseDao,
    LecturerExpertisePersistencePendingError,
)
from .dto import (
    LecturerExpertiseValidationError,
    ReplaceLecturerExpertiseDTO,
)
from .service import LecturerExpertiseService

LOGGER = logging.getLogger(__name__)
JSON_HEADERS = {"content-type": "application/json; charset=utf-8"}


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(body, ensure_ascii=False, separators=(",", ":")),
    }


def _method(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    return str(http.get("method") or event.get("httpMethod") or "GET").upper()


def _path(event: dict[str, Any]) -> str:
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    raw_path = event.get("rawPath") or http.get("path") or event.get("path") or "/"
    return str(raw_path).rstrip("/") or "/"


def _route(path: str) -> tuple[str, str, str | None] | None:
    parts = path.strip("/").split("/")
    if (
        len(parts) not in {5, 6}
        or parts[:3] != ["api", "v2", "lecturers"]
        or not parts[3]
        or parts[4] != "expertise"
    ):
        return None

    if len(parts) == 5:
        return "collection", parts[3], None
    if not parts[5]:
        return None
    return "detail", parts[3], parts[5]


def _request_payload(event: dict[str, Any]) -> Any:
    raw_body = event.get("body")
    if not isinstance(raw_body, str):
        raise LecturerExpertiseValidationError(
            None,
            "Request body must be a JSON object",
        )

    if event.get("isBase64Encoded"):
        try:
            raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as error:
            raise LecturerExpertiseValidationError(
                None,
                "Request body must be valid JSON",
            ) from error

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as error:
        raise LecturerExpertiseValidationError(
            None,
            "Request body must be valid JSON",
        ) from error


def _invalid_body_response(error: LecturerExpertiseValidationError) -> dict[str, Any]:
    error_body: dict[str, Any] = {
        "code": "INVALID_BODY",
        "message": str(error),
    }
    if error.field is not None:
        error_body["details"] = {"field": error.field}
    return _response(400, {"error": error_body})


def _not_implemented_response(
    error: LecturerExpertisePersistencePendingError,
) -> dict[str, Any]:
    return _response(
        501,
        {"error": {"code": "NOT_IMPLEMENTED", "message": str(error)}},
    )


def handle_request(
    event: dict[str, Any],
    service: LecturerExpertiseService | None = None,
) -> dict[str, Any]:
    path = _path(event)
    route = _route(path)
    if route is None:
        return _response(
            404,
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Lecturer expertise route not found",
                }
            },
        )

    route_type, lecturer_id, expertise_id = route
    method = _method(event)
    allowed_methods = {"GET", "PUT"} if route_type == "collection" else {"DELETE"}
    if method not in allowed_methods:
        return _response(
            405,
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": (
                        f"Only {', '.join(sorted(allowed_methods))} are supported "
                        f"for lecturer expertise {route_type}"
                    ),
                }
            },
        )

    active_service = service or LecturerExpertiseService(
        DeferredLecturerExpertiseDao()
    )

    if method == "GET":
        try:
            items = active_service.list_for_lecturer(lecturer_id)
        except LecturerExpertisePersistencePendingError as error:
            return _not_implemented_response(error)
        except Exception:
            LOGGER.exception("Unhandled lecturer expertise listing error")
            return _response(
                500,
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unable to list lecturer expertise",
                    }
                },
            )
        return _response(
            200,
            {
                "items": [item.to_dict() for item in items],
                "meta": {"count": len(items)},
            },
        )

    if method == "PUT":
        try:
            expertise = ReplaceLecturerExpertiseDTO.from_mapping(
                _request_payload(event)
            )
        except LecturerExpertiseValidationError as error:
            return _invalid_body_response(error)

        try:
            items = active_service.replace_for_lecturer(lecturer_id, expertise)
        except LecturerExpertisePersistencePendingError as error:
            return _not_implemented_response(error)
        except Exception:
            LOGGER.exception("Unhandled lecturer expertise replacement error")
            return _response(
                500,
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unable to replace lecturer expertise",
                    }
                },
            )
        return _response(
            200,
            {
                "items": [item.to_dict() for item in items],
                "meta": {"count": len(items)},
            },
        )

    if expertise_id is None:
        return _response(
            404,
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Lecturer expertise route not found",
                }
            },
        )

    try:
        active_service.remove_for_lecturer(lecturer_id, expertise_id)
    except LecturerExpertisePersistencePendingError as error:
        return _not_implemented_response(error)
    except Exception:
        LOGGER.exception("Unhandled lecturer expertise removal error")
        return _response(
            500,
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to remove lecturer expertise",
                }
            },
        )
    return {"statusCode": 204, "headers": JSON_HEADERS, "body": ""}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return handle_request(event)
