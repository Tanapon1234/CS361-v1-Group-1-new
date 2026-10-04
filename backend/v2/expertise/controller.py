"""HTTP Lambda controller for POST /api/v2/expertise."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Any

from .dao import (
    DeferredExpertiseDao,
    ExpertiseNotFoundError,
    ExpertisePersistencePendingError,
)
from .dto import (
    CreateExpertiseDTO,
    ExpertiseValidationError,
    PatchExpertiseDTO,
)
from .service import ExpertiseService

LOGGER = logging.getLogger(__name__)
JSON_HEADERS = {"content-type": "application/json; charset=utf-8"}
EXPERTISE_PATH = "/api/v2/expertise"


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


def _expertise_id(path: str) -> str | None:
    prefix = f"{EXPERTISE_PATH}/"
    if not path.startswith(prefix):
        return None
    expertise_id = path[len(prefix) :]
    if not expertise_id or "/" in expertise_id:
        return None
    return expertise_id


def _request_payload(event: dict[str, Any]) -> Any:
    raw_body = event.get("body")
    if not isinstance(raw_body, str):
        raise ExpertiseValidationError(None, "Request body must be a JSON object")

    if event.get("isBase64Encoded"):
        try:
            raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as error:
            raise ExpertiseValidationError(None, "Request body must be valid JSON") from error

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as error:
        raise ExpertiseValidationError(None, "Request body must be valid JSON") from error


def handle_request(
    event: dict[str, Any],
    service: ExpertiseService | None = None,
) -> dict[str, Any]:
    path = _path(event)
    expertise_id = _expertise_id(path)
    if path != EXPERTISE_PATH and expertise_id is None:
        return _response(
            404,
            {"error": {"code": "NOT_FOUND", "message": "Expertise route not found"}},
        )

    method = _method(event)
    if method not in {"GET", "POST", "PATCH"}:
        return _response(
            405,
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Only GET, POST, and PATCH are supported",
                }
            },
        )

    if expertise_id is not None and method not in {"GET", "PATCH"}:
        return _response(
            405,
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Only GET and PATCH are supported for expertise details",
                }
            },
        )

    if method == "PATCH" and expertise_id is None:
        return _response(
            405,
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "PATCH requires an expertise ID",
                }
            },
        )

    active_service = service or ExpertiseService(DeferredExpertiseDao())

    if method == "PATCH":
        try:
            expertise = PatchExpertiseDTO.from_mapping(_request_payload(event))
        except ExpertiseValidationError as error:
            error_body: dict[str, Any] = {
                "code": "INVALID_BODY",
                "message": str(error),
            }
            if error.field is not None:
                error_body["details"] = {"field": error.field}
            return _response(400, {"error": error_body})

        try:
            item = active_service.update(expertise_id, expertise)
        except ExpertiseNotFoundError as error:
            return _response(
                404,
                {"error": {"code": "EXPERTISE_NOT_FOUND", "message": str(error)}},
            )
        except ExpertisePersistencePendingError as error:
            return _response(
                501,
                {"error": {"code": "NOT_IMPLEMENTED", "message": str(error)}},
            )
        except Exception:
            LOGGER.exception("Unhandled expertise update error")
            return _response(
                500,
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unable to update expertise",
                    }
                },
            )
        return _response(200, {"item": item.to_dict()})

    if method == "GET":
        try:
            if expertise_id is not None:
                item = active_service.get_by_id(expertise_id)
                return _response(200, {"item": item.to_dict()})
            items = active_service.list_all()
        except ExpertiseNotFoundError as error:
            return _response(
                404,
                {"error": {"code": "EXPERTISE_NOT_FOUND", "message": str(error)}},
            )
        except ExpertisePersistencePendingError as error:
            return _response(
                501,
                {"error": {"code": "NOT_IMPLEMENTED", "message": str(error)}},
            )
        except Exception:
            LOGGER.exception("Unhandled expertise listing error")
            return _response(
                500,
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Unable to list expertise",
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

    try:
        expertise = CreateExpertiseDTO.from_mapping(_request_payload(event))
    except ExpertiseValidationError as error:
        error_body: dict[str, Any] = {
            "code": "INVALID_BODY",
            "message": str(error),
        }
        if error.field is not None:
            error_body["details"] = {"field": error.field}
        return _response(400, {"error": error_body})

    try:
        item = active_service.create(expertise)
    except ExpertisePersistencePendingError as error:
        return _response(
            501,
            {"error": {"code": "NOT_IMPLEMENTED", "message": str(error)}},
        )
    except Exception:
        LOGGER.exception("Unhandled expertise creation error")
        return _response(
            500,
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Unable to create expertise",
                }
            },
        )
    return _response(201, {"item": item})


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return handle_request(event)
