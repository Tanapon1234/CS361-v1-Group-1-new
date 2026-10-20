from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.v3.controllers.params import SubmissionId
from app.v3.dependencies import CurrentActorDep, CurrentLecturerIdDep, SubmissionServiceDep
from app.v3.dtos.common import ListResponse, PageResponse
from app.v3.dtos.submission_dto import (
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
    actor: CurrentActorDep,
    service: SubmissionServiceDep,
) -> PageResponse[SubmissionResponse]:
    """Your own; a department's for its chair / committee; all for viewers."""
    return service.list_submissions(actor, query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_submission(
    data: SubmissionCreateRequest, actor_id: CurrentLecturerIdDep, service: SubmissionServiceDep
) -> SubmissionResponse:
    """Create the caller's own submission for an open round."""
    return service.create_submission(actor_id, data)


@router.get("/{submission_id}")
def get_submission(
    submission_id: SubmissionId, actor: CurrentActorDep, service: SubmissionServiceDep
) -> SubmissionDetailResponse:
    """The submission with all its entries."""
    return service.get_submission(submission_id, actor)


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: SubmissionId, actor_id: CurrentLecturerIdDep, service: SubmissionServiceDep
) -> None:
    """Only a draft."""
    service.delete_submission(submission_id, actor_id)


@router.get("/{submission_id}/summary")
def get_submission_summary(
    submission_id: SubmissionId, actor: CurrentActorDep, service: SubmissionServiceDep
) -> SubmissionSummaryResponse:
    """Totals computed now from the entries, with the minimum-requirement checks."""
    return service.get_summary(submission_id, actor)


@router.get("/{submission_id}/totals")
def get_submission_totals(
    submission_id: SubmissionId, actor: CurrentActorDep, service: SubmissionServiceDep
) -> SubmissionTotalsResponse:
    """Category totals frozen when the submission was sent."""
    return service.get_totals(submission_id, actor)


@router.get(
    "/{submission_id}/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "The form as PDF"}},
)
def get_submission_pdf(
    submission_id: SubmissionId, actor: CurrentActorDep, service: SubmissionServiceDep
) -> Response:
    return Response(service.get_pdf(submission_id, actor), media_type="application/pdf")


@router.get("/{submission_id}/approvals")
def list_submission_approvals(
    submission_id: SubmissionId, actor: CurrentActorDep, service: SubmissionServiceDep
) -> ListResponse[ApprovalResponse]:
    """Every send, return and sign-off, oldest first."""
    return service.list_approvals(submission_id, actor)


@router.post("/{submission_id}/approvals", status_code=status.HTTP_201_CREATED)
def create_submission_approval(
    submission_id: SubmissionId,
    data: ApprovalCreateRequest,
    actor: CurrentActorDep,
    service: SubmissionServiceDep,
) -> ApprovalResponse:
    """Send / accept / return / approve. The step (from the current status) decides who may
    sign: the owner, staff (receiver), or the chair / committee of the department."""
    return service.create_approval(submission_id, actor, data)
