"""`/api/v2`: collects every v2 controller.

A future version lives in its own folder (e.g. `app/v3/`) with its own router,
and is included next to this one in app/main.py.
"""

from typing import Any

from fastapi import APIRouter

from app.core.problem import ProblemDetail
from app.v2.controllers import (
    assessment_controller,
    cv_controller,
    department_controller,
    education_controller,
    entry_controller,
    evidence_controller,
    expertise_controller,
    lecturer_controller,
    lecturer_expertise_controller,
    lecturer_publication_controller,
    lecturer_research_interest_controller,
    me_controller,
    position_controller,
    profile_image_controller,
    publication_controller,
    publication_profile_controller,
    research_interest_controller,
    round_controller,
    rubric_controller,
    submission_controller,
)

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ProblemDetail, "description": "Business rule violated"},
    401: {"model": ProblemDetail, "description": "No caller identity"},
    403: {"model": ProblemDetail, "description": "The caller may not do this"},
    404: {"model": ProblemDetail, "description": "Resource not found"},
    409: {"model": ProblemDetail, "description": "Conflicts with existing data or state"},
    412: {"model": ProblemDetail, "description": "If-Match does not match the current ETag"},
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
    # workload (SemesterReport)
    me_controller,
    department_controller,
    position_controller,
    rubric_controller,
    round_controller,
    submission_controller,
    entry_controller,
    assessment_controller,
    evidence_controller,
):
    api_v2_router.include_router(controller.router)
