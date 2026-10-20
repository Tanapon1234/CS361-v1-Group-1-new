"""Everything one lecturer did in a year (workload entries + publications)."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.v3.controllers.params import LecturerId
from app.v3.dependencies import CurrentActorDep, LecturerWorkServiceDep
from app.v3.dtos.lecturer_work_dto import LecturerWorkQuery, LecturerWorkResponse

router = APIRouter(prefix="/lecturers/{lecturer_id}/work", tags=["lecturer-work"])


@router.get("")
def get_lecturer_work(
    lecturer_id: LecturerId,
    query: Annotated[LecturerWorkQuery, Query()],
    actor: CurrentActorDep,
    service: LecturerWorkServiceDep,
) -> LecturerWorkResponse:
    """Filter by `academic_year` (B.E.) and/or rubric `category` code. An empty result still
    returns `filters` and `available_years`, so the client can say what was searched."""
    return service.get_work(lecturer_id, actor, query)
