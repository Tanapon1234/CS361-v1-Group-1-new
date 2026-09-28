"""`/api/v2`: collects every v2 controller.

A future version lives in its own folder (e.g. `app/v3/`) with its own router,
and is included next to this one in app/main.py.
"""

from typing import Any

from fastapi import APIRouter

from app.core.problem import ProblemDetail
from app.v2.controllers import (
    cv_controller,
    education_controller,
    expertise_controller,
    lecturer_controller,
    lecturer_expertise_controller,
    lecturer_publication_controller,
    lecturer_research_interest_controller,
    profile_image_controller,
    publication_controller,
    publication_profile_controller,
    research_interest_controller,
)

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ProblemDetail, "description": "Business rule violated"},
    404: {"model": ProblemDetail, "description": "Resource not found"},
    409: {"model": ProblemDetail, "description": "Conflicts with existing data"},
    422: {"model": ProblemDetail, "description": "Invalid request fields"},
}

api_v2_router = APIRouter(prefix="/api/v2", responses=ERROR_RESPONSES)

for controller in (
    lecturer_controller,
    profile_image_controller,
    cv_controller,
    education_controller,
    research_interest_controller,
    lecturer_research_interest_controller,
    publication_profile_controller,
    publication_controller,
    lecturer_publication_controller,
    expertise_controller,
    lecturer_expertise_controller,
):
    api_v2_router.include_router(controller.router)
