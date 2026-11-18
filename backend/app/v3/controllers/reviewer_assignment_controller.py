from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v3.controllers.params import ReviewerAssignmentId
from app.v3.dependencies import CurrentActorDep, ReviewerAssignmentServiceDep
from app.v3.dtos.common import ListResponse
from app.v3.dtos.reviewer_assignment_dto import (
    ReviewerAssignmentCreateRequest,
    ReviewerAssignmentListQuery,
    ReviewerAssignmentResponse,
)

router = APIRouter(prefix="/reviewer-assignments", tags=["reviewer-assignments"])


@router.get("")
def list_reviewer_assignments(
    query: Annotated[ReviewerAssignmentListQuery, Query()],
    actor: CurrentActorDep,
    service: ReviewerAssignmentServiceDep,
) -> ListResponse[ReviewerAssignmentResponse]:
    """Executive/admin see any (optionally filtered); a reviewer sees only their own."""
    return service.list_assignments(actor, query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reviewer_assignment(
    data: ReviewerAssignmentCreateRequest,
    actor: CurrentActorDep,
    service: ReviewerAssignmentServiceDep,
) -> ReviewerAssignmentResponse:
    """Executive/admin only (ROUTE_RULES): assign a reviewer to a lecturer."""
    return service.create_assignment(actor, data)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reviewer_assignment(
    assignment_id: ReviewerAssignmentId, service: ReviewerAssignmentServiceDep
) -> None:
    service.delete_assignment(assignment_id)
