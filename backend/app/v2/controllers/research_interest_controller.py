"""Master list of research interests."""

from typing import Annotated

from fastapi import APIRouter, Body, Query, status
from pydantic import ValidationError

from app.v2.controllers.params import ResearchInterestId
from app.v2.dependencies import ResearchInterestServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.research_interest_dto import (
    ResearchInterestCreateRequest,
    ResearchInterestListQuery,
    ResearchInterestListResponse,
    ResearchInterestResponse,
    ResearchInterestUpdateRequest,
)

router = APIRouter(prefix="/research-interests", tags=["research-interests"])


@router.get("")
def list_research_interests(
    query: Annotated[ResearchInterestListQuery, Query()],
    service: ResearchInterestServiceDep,
) -> PageResponse[ResearchInterestResponse]:
    return service.list_research_interests(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_research_interest(
    data: ResearchInterestCreateRequest, service: ResearchInterestServiceDep
) -> ResearchInterestResponse:
    return service.create_research_interest(data)


@router.patch("/{research_interest_id}")
def update_research_interest(
    research_interest_id: ResearchInterestId,
    data: ResearchInterestUpdateRequest,
    service: ResearchInterestServiceDep,
) -> ResearchInterestResponse:
    return service.update_research_interest(research_interest_id, data)


@router.delete("/{research_interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_interest(
    research_interest_id: ResearchInterestId, service: ResearchInterestServiceDep
) -> None:
    service.delete_research_interest(research_interest_id)
