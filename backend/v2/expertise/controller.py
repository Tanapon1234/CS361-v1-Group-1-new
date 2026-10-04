"""HTTP Lambda controller for POST /api/v2/expertise."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import Any

from .dao import DeferredExpertiseDao, ExpertisePersistencePendingError
from .dto import CreateExpertiseDTO, ExpertiseValidationError
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


def _request_dto(event: dict[str, Any]) -> CreateExpertiseDTO:
    raw_body = event.get("body")
    if not isinstance(raw_body, str):
        raise ExpertiseValidationError(None, "Request body must be a JSON object")

    if event.get("isBase64Encoded"):
        try:
            raw_body = base64.b64decode(raw_body, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as error:
            raise ExpertiseValidationError(None, "Request body must be valid JSON") from error

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as error:
        raise ExpertiseValidationError(None, "Request body must be valid JSON") from error
    return CreateExpertiseDTO.from_mapping(payload)


def handle_request(
    event: dict[str, Any],
    service: ExpertiseService | None = None,
) -> dict[str, Any]:
    if _path(event) != EXPERTISE_PATH:
        return _response(
            404,
            {"error": {"code": "NOT_FOUND", "message": "Expertise route not found"}},
        )

    if _method(event) != "POST":
        return _response(
            405,
            {"error": {"code": "METHOD_NOT_ALLOWED", "message": "Only POST is supported"}},
        )

    try:
        expertise = _request_dto(event)
    except ExpertiseValidationError as error:
        error_body: dict[str, Any] = {
            "code": "INVALID_BODY",
            "message": str(error),
        }
        if error.field is not None:
            error_body["details"] = {"field": error.field}
        return _response(400, {"error": error_body})

    active_service = service or ExpertiseService(DeferredExpertiseDao())
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
