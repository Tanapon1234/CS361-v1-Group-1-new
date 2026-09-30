"""Research interests assigned to one lecturer."""

from uuid import UUID

from fastapi import APIRouter, status
from pydantic import ValidationError

from app.core.exceptions import BadRequestError
from app.v2.controllers.params import LecturerId, ResearchInterestId
from app.v2.dependencies import ResearchInterestServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestListQuery,
    LecturerResearchInterestListResponse,
    LecturerResearchInterestsReplaceRequest,
    ResearchInterestResponse,
)

router = APIRouter(
    prefix="/lecturers/{lecturer_id}/research-interests", tags=["research-interests"]
)


@router.get("")
def list_lecturer_research_interests(
    lecturer_id: str,
    service: ResearchInterestServiceDep,
    search: str | None = None,
    sort_order: str = "asc",
) -> LecturerResearchInterestListResponse:
    try:
        parsed_lecturer_id = UUID(lecturer_id)
        query = LecturerResearchInterestListQuery.model_validate(
            {"search": search, "sort_order": sort_order}
        )
    except (ValueError, ValidationError) as exc:
        raise BadRequestError("Path or query parameters are invalid") from exc

    return service.list_lecturer_research_interests(parsed_lecturer_id, query)


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
