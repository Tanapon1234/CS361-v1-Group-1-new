"""Research interests assigned to one lecturer."""

from fastapi import APIRouter, status

from app.v2.controllers.params import LecturerId, ResearchInterestId
from app.v2.dependencies import ResearchInterestServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestsReplaceRequest,
    ResearchInterestResponse,
)

router = APIRouter(
    prefix="/lecturers/{lecturer_id}/research-interests", tags=["research-interests"]
)


@router.get("")
def list_lecturer_research_interests(
    lecturer_id: LecturerId, service: ResearchInterestServiceDep
) -> ListResponse[ResearchInterestResponse]:
    return service.list_lecturer_research_interests(lecturer_id)


@router.put("")
def replace_lecturer_research_interests(
    lecturer_id: LecturerId,
    data: LecturerResearchInterestsReplaceRequest,
    service: ResearchInterestServiceDep,
) -> ListResponse[ResearchInterestResponse]:
    """Replace the lecturer's whole set of research interests."""
    return service.replace_lecturer_research_interests(lecturer_id, data)


@router.delete("/{research_interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lecturer_research_interest(
    lecturer_id: LecturerId,
    research_interest_id: ResearchInterestId,
    service: ResearchInterestServiceDep,
) -> None:
    service.remove_lecturer_research_interest(lecturer_id, research_interest_id)
