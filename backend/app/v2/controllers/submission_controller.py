from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.v2.controllers.params import SubmissionId
from app.v2.dependencies import CurrentLecturerIdDep, SubmissionServiceDep
from app.v2.dtos.common import ListResponse, PageResponse
from app.v2.dtos.submission_dto import (
    ApprovalCreateRequest,
    ApprovalResponse,
    SubmissionCreateRequest,
    SubmissionDetailResponse,
    SubmissionListQuery,
    SubmissionResponse,
    SubmissionSummaryResponse,
    SubmissionTotalsResponse,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("")
def list_submissions(
    query: Annotated[SubmissionListQuery, Query()],
    actor_id: CurrentLecturerIdDep,
    service: SubmissionServiceDep,
) -> PageResponse[SubmissionResponse]:
    return service.list_submissions(actor_id, query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_submission(
    data: SubmissionCreateRequest, actor_id: CurrentLecturerIdDep, service: SubmissionServiceDep
) -> SubmissionResponse:
    """Create the caller's own submission for an open round."""
    return service.create_submission(actor_id, data)


@router.get("/{submission_id}")
def get_submission(
    submission_id: SubmissionId, service: SubmissionServiceDep
) -> SubmissionDetailResponse:
    """The submission with all its entries."""
    return service.get_submission(submission_id)


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: SubmissionId, actor_id: CurrentLecturerIdDep, service: SubmissionServiceDep
) -> None:
    """Only a draft."""
    service.delete_submission(submission_id, actor_id)


@router.get("/{submission_id}/summary")
def get_submission_summary(
    submission_id: SubmissionId, service: SubmissionServiceDep
) -> SubmissionSummaryResponse:
    """Totals computed now from the entries, with the minimum-requirement checks."""
    return service.get_summary(submission_id)


@router.get("/{submission_id}/totals")
def get_submission_totals(
    submission_id: SubmissionId, service: SubmissionServiceDep
) -> SubmissionTotalsResponse:
    """Category totals frozen when the submission was sent."""
    return service.get_totals(submission_id)


@router.get(
    "/{submission_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "The form as PDF"}},
)
def get_submission_pdf(submission_id: SubmissionId, service: SubmissionServiceDep) -> Response:
    return Response(service.get_pdf(submission_id), media_type="application/pdf")


@router.get("/{submission_id}/approvals")
def list_submission_approvals(
    submission_id: SubmissionId, service: SubmissionServiceDep
) -> ListResponse[ApprovalResponse]:
    """Every send, return and sign-off, oldest first."""
    return service.list_approvals(submission_id)


@router.post("/{submission_id}/approvals", status_code=status.HTTP_201_CREATED)
def create_submission_approval(
    submission_id: SubmissionId,
    data: ApprovalCreateRequest,
    actor_id: CurrentLecturerIdDep,
    service: SubmissionServiceDep,
) -> ApprovalResponse:
    """Send / accept / return / approve. The signer's role comes from the current status."""
    return service.create_approval(submission_id, actor_id, data)
