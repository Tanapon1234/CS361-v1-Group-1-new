"""Application errors.

Services raise these; app/core/error_handlers.py turns them into RFC 9457
(formerly RFC 7807) problem responses. Never raise HTTPException from services.
"""


class AppError(Exception):
    status_code: int = 500
    title: str = "Internal Server Error"
    problem_type: str = "internal-error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail


class BadRequestError(AppError):
    """The request is well-formed but breaks a business rule (e.g. unsupported file type)."""

    status_code = 400
    title = "Bad Request"
    problem_type = "bad-request"


class NotFoundError(AppError):
    status_code = 404
    title = "Resource Not Found"
    problem_type = "not-found"


class ConflictError(AppError):
    """The change conflicts with existing data (e.g. duplicate email, resource still in use)."""

    status_code = 409
    title = "Conflict"
    problem_type = "conflict"


class ServiceUnavailableError(AppError):
    status_code = 503
    title = "Service Unavailable"
    problem_type = "service-unavailable"
