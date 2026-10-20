from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v3.controllers.params import EntryId
from app.v3.dependencies import AssessmentServiceDep, CurrentActorDep, CurrentLecturerIdDep
from app.v3.dtos.assessment_dto import (
    AssessmentPutRequest,
    AssessmentQueueItem,
    AssessmentQueueQuery,
    AssessmentResponse,
)
from app.v3.dtos.common import ListResponse, PageResponse

router = APIRouter(tags=["assessments"])


@router.get("/assessments")
def list_assessment_queue(
    query: Annotated[AssessmentQueueQuery, Query()],
    actor_id: CurrentLecturerIdDep,
    service: AssessmentServiceDep,
) -> PageResponse[AssessmentQueueItem]:
    """The caller's assessment to-do list (entries their positions may assess)."""
    return service.list_queue(actor_id, query)


@router.get("/entries/{entry_id}/assessments")
def list_entry_assessments(
    entry_id: EntryId, actor: CurrentActorDep, service: AssessmentServiceDep
) -> ListResponse[AssessmentResponse]:
    return service.list_entry_assessments(entry_id, actor)


@router.put("/entries/{entry_id}/assessments/me")
def put_my_assessment(
    entry_id: EntryId,
    data: AssessmentPutRequest,
    actor_id: CurrentLecturerIdDep,
    service: AssessmentServiceDep,
) -> AssessmentResponse:
    """Give or change the caller's value (one per assessor per entry)."""
    return service.put_my_assessment(entry_id, actor_id, data)


@router.delete("/entries/{entry_id}/assessments/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_assessment(
    entry_id: EntryId, actor_id: CurrentLecturerIdDep, service: AssessmentServiceDep
) -> None:
    service.delete_my_assessment(entry_id, actor_id)
