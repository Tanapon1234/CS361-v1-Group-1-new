from typing import Annotated

from fastapi import APIRouter, Header, Response, status
from fastapi.responses import RedirectResponse

from app.v2.controllers.params import EntryId, EvidenceId
from app.v2.dependencies import CurrentLecturerIdDep, EvidenceServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.evidence_dto import (
    EvidenceCreateRequest,
    EvidenceResponse,
    EvidenceUpdateRequest,
    EvidenceUploadResponse,
    evidence_etag,
)

router = APIRouter(tags=["evidence"])


@router.get("/entries/{entry_id}/evidence")
def list_evidence(entry_id: EntryId, service: EvidenceServiceDep) -> ListResponse[EvidenceResponse]:
    return service.list_evidence(entry_id)


@router.post("/entries/{entry_id}/evidence", status_code=status.HTTP_201_CREATED)
def create_evidence(
    entry_id: EntryId,
    data: EvidenceCreateRequest,
    actor_id: CurrentLecturerIdDep,
    service: EvidenceServiceDep,
) -> EvidenceUploadResponse:
    """Step 1: reserve a `pending` row and get a presigned S3 upload."""
    return service.create_evidence(entry_id, actor_id, data)


@router.patch("/evidence/{evidence_id}")
def update_evidence(
    evidence_id: EvidenceId,
    data: EvidenceUpdateRequest,
    actor_id: CurrentLecturerIdDep,
    service: EvidenceServiceDep,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> EvidenceResponse:
    """Step 3: `{"status": "uploaded", "checksum": "..."}` after uploading to S3."""
    evidence = service.update_evidence(evidence_id, actor_id, data, if_match)
    response.headers["ETag"] = evidence_etag(evidence)
    return evidence


@router.get(
    "/evidence/{evidence_id}/content",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    responses={302: {"description": "Redirect to a short-lived S3 download URL"}},
)
def get_evidence_content(evidence_id: EvidenceId, service: EvidenceServiceDep) -> RedirectResponse:
    download = service.get_download(evidence_id)
    return RedirectResponse(download.url, status_code=status.HTTP_302_FOUND)


@router.delete("/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    evidence_id: EvidenceId, actor_id: CurrentLecturerIdDep, service: EvidenceServiceDep
) -> None:
    """Deletes the row and the file in S3."""
    service.delete_evidence(evidence_id, actor_id)
