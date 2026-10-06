from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import RoundId
from app.v2.dependencies import RoundServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.round_dto import (
    RoundCreateRequest,
    RoundListQuery,
    RoundReportQuery,
    RoundReportResponse,
    RoundResponse,
    RoundSubmissionsQuery,
    RoundUpdateRequest,
)
from app.v2.dtos.submission_dto import SubmissionResponse

router = APIRouter(prefix="/rounds", tags=["rounds"])


@router.get("")
def list_rounds(
    query: Annotated[RoundListQuery, Query()], service: RoundServiceDep
) -> PageResponse[RoundResponse]:
    return service.list_rounds(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_round(data: RoundCreateRequest, service: RoundServiceDep) -> RoundResponse:
    return service.create_round(data)


@router.get("/{round_id}")
def get_round(round_id: RoundId, service: RoundServiceDep) -> RoundResponse:
    return service.get_round(round_id)


@router.patch("/{round_id}")
def update_round(
    round_id: RoundId, data: RoundUpdateRequest, service: RoundServiceDep
) -> RoundResponse:
    """Change dates, or open/close the round with `{"is_open": true|false}`."""
    return service.update_round(round_id, data)


@router.get("/{round_id}/submissions")
def list_round_submissions(
    round_id: RoundId,
    query: Annotated[RoundSubmissionsQuery, Query()],
    service: RoundServiceDep,
) -> PageResponse[SubmissionResponse]:
    return service.list_round_submissions(round_id, query)


@router.get("/{round_id}/report")
def get_round_report(
    round_id: RoundId, query: Annotated[RoundReportQuery, Query()], service: RoundServiceDep
) -> RoundReportResponse:
    """Scores of every submission in the round, for the dashboard."""
    return service.get_report(round_id, query)
