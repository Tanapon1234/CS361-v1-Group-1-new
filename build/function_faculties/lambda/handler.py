"""Lambda entrypoint for the Faculty read API.

Routes (GET only):
    GET /api/v1/faculties        -> {"data": [...]}
    GET /api/v1/faculties/{id}   -> {"data": {...}}

Environment variables:
    DATA_BUCKET_NAME  required, per-environment bucket
    SERVING_PREFIX    optional, default "serving"
    LOG_LEVEL         optional, default "INFO"
    ENVIRONMENT       optional, log context only (dev/staging/prod)
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Optional, Tuple

import responses
from faculty_service import BackendDataError, FacultyNotFoundError, FacultyService
from s3_repository import S3Repository
from validation import InvalidFacultyIdError

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
ENVIRONMENT = os.environ.get("ENVIRONMENT", "unknown")

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

LIST_PATH_PATTERN = re.compile(r"^/api/v1/faculties/?$")
DETAIL_PATH_PATTERN = re.compile(r"^/api/v1/faculties/([^/]*)/?$")

_service: Optional[FacultyService] = None


# --------------------------------------------------------------------- setup
def build_service() -> FacultyService:
    bucket = os.environ.get("DATA_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("DATA_BUCKET_NAME is not configured")
    prefix = os.environ.get("SERVING_PREFIX", "serving")
    return FacultyService(S3Repository(bucket=bucket, prefix=prefix))


def get_service() -> FacultyService:
    """Cached across warm invocations; ``reset_service()`` clears it in tests."""
    global _service
    if _service is None:
        _service = build_service()
    return _service


def reset_service() -> None:
    global _service
    _service = None


def set_service(service: Optional[FacultyService]) -> None:
    """Dependency injection hook for unit tests / local invokes."""
    global _service
    _service = service


# ------------------------------------------------------------------- parsing
def _extract_method(event: Dict[str, Any]) -> str:
    method = event.get("httpMethod")
    if not method:
        method = (
            event.get("requestContext", {}).get("http", {}).get("method")
            or event.get("requestContext", {}).get("httpMethod")
        )
    return (method or "GET").upper()


def _extract_path(event: Dict[str, Any]) -> str:
    path = event.get("path") or event.get("rawPath") or event.get("resource") or "/"
    stage = event.get("requestContext", {}).get("stage")
    if stage and stage != "$default" and path.startswith(f"/{stage}/"):
        path = path[len(stage) + 1:]
    return path or "/"


def _path_parameter_id(event: Dict[str, Any]) -> Optional[str]:
    params = event.get("pathParameters") or {}
    if not isinstance(params, dict):
        return None
    for key in ("id", "facultyId", "faculty_id"):
        if key in params and params[key] is not None:
            return params[key]
    return None


def route(event: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Return ``("list"|"detail"|"unknown", faculty_id_or_None)``."""
    path = _extract_path(event)

    if LIST_PATH_PATTERN.match(path):
        return "list", None

    detail_match = DETAIL_PATH_PATTERN.match(path)
    if detail_match:
        faculty_id = _path_parameter_id(event)
        if faculty_id is None:
            faculty_id = detail_match.group(1)
        return "detail", faculty_id

    return "unknown", None


# ------------------------------------------------------------------- handler
def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    event = event or {}
    method = _extract_method(event)
    path = _extract_path(event)
    action, faculty_id = route(event)

    logger.info("request env=%s method=%s path=%s action=%s", ENVIRONMENT, method, path, action)

    try:
        if action == "unknown":
            logger.info("route_not_found method=%s path=%s", method, path)
            return responses.not_found(responses.ROUTE_NOT_FOUND)

        if method != "GET":
            logger.info("method_not_allowed method=%s path=%s", method, path)
            return responses.method_not_allowed("GET")

        service = get_service()

        if action == "list":
            data = service.list_faculties()
            logger.info("list_success count=%d", len(data))
            return responses.ok(data)

        # detail
        faculty = service.get_faculty(faculty_id)
        logger.info("detail_success faculty_id=%s", faculty_id)
        return responses.ok(faculty)

    except InvalidFacultyIdError as exc:
        logger.info("invalid_faculty_id reason=%s", exc.reason)
        return responses.bad_request()

    except FacultyNotFoundError:
        logger.info("faculty_not_found faculty_id=%s", faculty_id)
        return responses.not_found()

    except BackendDataError as exc:
        logger.error("backend_data_error reason=%s", exc.reason)
        return responses.internal_error()

    except Exception as exc:  # noqa: BLE001 - last resort, nothing leaks out
        logger.exception("unhandled_error error_type=%s", exc.__class__.__name__)
        return responses.internal_error()


# Common alternative entrypoint name.
handler = lambda_handler
