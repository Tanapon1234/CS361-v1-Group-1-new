"""Turn every error into an `application/problem+json` response (RFC 9457 / RFC 7807)."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.problem import FieldError, ProblemDetail

logger = logging.getLogger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"
# Stable, documented identifiers for each problem type (see backend/README.md).
PROBLEM_TYPE_PREFIX = "urn:cs361:problem:"


def _slug(status_code: int) -> str:
    return HTTPStatus(status_code).phrase.lower().replace(" ", "-")


def _problem(
    request: Request,
    *,
    status_code: int,
    title: str,
    problem_type: str,
    detail: str | None = None,
    errors: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ProblemDetail(
        type=PROBLEM_TYPE_PREFIX + problem_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=request.url.path,
        errors=errors,
    )
    return JSONResponse(
        body.model_dump(mode="json", exclude_none=True),
        status_code=status_code,
        media_type=PROBLEM_CONTENT_TYPE,
        headers=headers,
    )


async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _problem(
        request,
        status_code=exc.status_code,
        title=exc.title,
        problem_type=exc.problem_type,
        detail=exc.detail,
    )


async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        FieldError(field=".".join(str(part) for part in error["loc"]), message=error["msg"])
        for error in exc.errors()
    ]
    return _problem(
        request,
        status_code=422,
        title="Validation Error",
        problem_type="validation-error",
        detail="The request contains invalid fields.",
        errors=errors,
    )


async def _http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _problem(
        request,
        status_code=exc.status_code,
        title=HTTPStatus(exc.status_code).phrase,
        problem_type=_slug(exc.status_code),
        detail=exc.detail if isinstance(exc.detail, str) else None,
        headers=exc.headers,
    )


async def _not_implemented_handler(request: Request, exc: NotImplementedError) -> JSONResponse:
    return _problem(
        request,
        status_code=501,
        title="Not Implemented",
        problem_type="not-implemented",
        detail="This endpoint is scaffolded but not implemented yet.",
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _problem(
        request,
        status_code=500,
        title="Internal Server Error",
        problem_type="internal-error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)
    app.add_exception_handler(NotImplementedError, _not_implemented_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
