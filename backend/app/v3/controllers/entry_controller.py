from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.v3.controllers.params import EntryId, SubmissionId
from app.v3.dependencies import CurrentActorDep, EntryServiceDep
from app.v3.dtos.common import ListResponse
from app.v3.dtos.submission_dto import (
    EntryCreateRequest,
    EntryListQuery,
    EntryResponse,
    EntryUpdateRequest,
    entry_etag,
)

router = APIRouter(tags=["entries"])


@router.get("/submissions/{submission_id}/entries")
def list_entries(
    submission_id: SubmissionId,
    query: Annotated[EntryListQuery, Query()],
    actor: CurrentActorDep,
    service: EntryServiceDep,
) -> ListResponse[EntryResponse]:
    return service.list_entries(submission_id, actor, query)


@router.post("/submissions/{submission_id}/entries", status_code=status.HTTP_201_CREATED)
def create_entry(
    submission_id: SubmissionId,
    data: EntryCreateRequest,
    actor: CurrentActorDep,
    service: EntryServiceDep,
    response: Response,
) -> EntryResponse:
    """Add one line; the response has the score the server computed. Staff may draft one
    for a lecturer in their own department, pending that lecturer's confirmation."""
    entry = service.create_entry(submission_id, actor, data)
    response.headers["ETag"] = entry_etag(entry)
    return entry


@router.get("/entries/{entry_id}")
def get_entry(
    entry_id: EntryId, actor: CurrentActorDep, service: EntryServiceDep, response: Response
) -> EntryResponse:
    entry = service.get_entry(entry_id, actor)
    response.headers["ETag"] = entry_etag(entry)
    return entry


@router.patch("/entries/{entry_id}")
def update_entry(
    entry_id: EntryId,
    data: EntryUpdateRequest,
    actor: CurrentActorDep,
    service: EntryServiceDep,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> EntryResponse:
    """Draft or returned submissions only. 412 if `If-Match` is not the current ETag."""
    entry = service.update_entry(entry_id, actor, data, if_match)
    response.headers["ETag"] = entry_etag(entry)
    return entry


@router.post("/entries/{entry_id}/confirm")
def confirm_entry(
    entry_id: EntryId, actor: CurrentActorDep, service: EntryServiceDep, response: Response
) -> EntryResponse:
    """The owner confirms a staff-drafted entry (V4 #292); staff cannot confirm their own."""
    entry = service.confirm_entry(entry_id, actor)
    response.headers["ETag"] = entry_etag(entry)
    return entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: EntryId, actor: CurrentActorDep, service: EntryServiceDep) -> None:
    service.delete_entry(entry_id, actor)
