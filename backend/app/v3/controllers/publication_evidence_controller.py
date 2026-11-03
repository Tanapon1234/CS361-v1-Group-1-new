from typing import Annotated

from fastapi import APIRouter, Header, Response, status
from fastapi.responses import RedirectResponse

from app.v3.controllers.params import EvidenceId, PublicationId
from app.v3.dependencies import CurrentActorDep, PublicationEvidenceServiceDep
from app.v3.dtos.common import ListResponse
from app.v3.dtos.publication_evidence_dto import (
    PublicationEvidenceCreateRequest,
    PublicationEvidenceResponse,
    PublicationEvidenceUpdateRequest,
    PublicationEvidenceUploadResponse,
    publication_evidence_etag,
)

router = APIRouter(prefix="/publications/{publication_id}/evidence", tags=["publication-evidence"])


@router.get("")
def list_publication_evidence(
    publication_id: PublicationId, service: PublicationEvidenceServiceDep
) -> ListResponse[PublicationEvidenceResponse]:
    return service.list_evidence(publication_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_publication_evidence(
    publication_id: PublicationId,
    data: PublicationEvidenceCreateRequest,
    actor: CurrentActorDep,
    service: PublicationEvidenceServiceDep,
) -> PublicationEvidenceUploadResponse:
    """Step 1: reserve a `pending` row and get a presigned S3 upload."""
    return service.create_evidence(publication_id, actor, data)


@router.patch("/{evidence_id}")
def update_publication_evidence(
    publication_id: PublicationId,
    evidence_id: EvidenceId,
    data: PublicationEvidenceUpdateRequest,
    actor: CurrentActorDep,
    service: PublicationEvidenceServiceDep,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> PublicationEvidenceResponse:
    """Step 3: `{"status": "uploaded", "checksum": "..."}` after uploading to S3."""
    evidence = service.update_evidence(publication_id, evidence_id, actor, data, if_match)
    response.headers["ETag"] = publication_evidence_etag(evidence)
    return evidence


@router.get(
    "/{evidence_id}/content",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    responses={302: {"description": "Redirect to a short-lived S3 download URL"}},
)
def get_publication_evidence_content(
    publication_id: PublicationId, evidence_id: EvidenceId, service: PublicationEvidenceServiceDep
) -> RedirectResponse:
    download = service.get_download(publication_id, evidence_id)
    return RedirectResponse(download.url, status_code=status.HTTP_302_FOUND)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication_evidence(
    publication_id: PublicationId,
    evidence_id: EvidenceId,
    actor: CurrentActorDep,
    service: PublicationEvidenceServiceDep,
) -> None:
    """Deletes the row and the file in S3."""
    service.delete_evidence(publication_id, evidence_id, actor)
