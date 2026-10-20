"""Reviewers verify or reject publications and evidence files (migration 005)."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.v2.controllers.params import EvidenceId, PublicationId
from app.v2.dependencies import CurrentActorDep, VerificationServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.verification_dto import (
    EvidenceQueueItem,
    PublicationQueueItem,
    VerificationPutRequest,
    VerificationQueueQuery,
    VerificationResponse,
)

router = APIRouter(tags=["verification"])


@router.get("/publications/{publication_id}/verification")
def get_publication_verification(
    publication_id: PublicationId, service: VerificationServiceDep
) -> VerificationResponse:
    return service.get_publication_verification(publication_id)


@router.put("/publications/{publication_id}/verification")
def set_publication_verification(
    publication_id: PublicationId,
    data: VerificationPutRequest,
    actor: CurrentActorDep,
    service: VerificationServiceDep,
) -> VerificationResponse:
    """Reviewers: verified / rejected (with a note) / back to pending. Not your own work."""
    return service.set_publication_verification(publication_id, actor, data)


@router.get("/evidence/{evidence_id}/verification")
def get_evidence_verification(
    evidence_id: EvidenceId, actor: CurrentActorDep, service: VerificationServiceDep
) -> VerificationResponse:
    return service.get_evidence_verification(evidence_id, actor)


@router.put("/evidence/{evidence_id}/verification")
def set_evidence_verification(
    evidence_id: EvidenceId,
    data: VerificationPutRequest,
    actor: CurrentActorDep,
    service: VerificationServiceDep,
) -> VerificationResponse:
    """Reviewers: an uploaded file only, not of your own submission."""
    return service.set_evidence_verification(evidence_id, actor, data)


@router.get("/verifications/publications")
def list_publication_verification_queue(
    query: Annotated[VerificationQueueQuery, Query()], service: VerificationServiceDep
) -> PageResponse[PublicationQueueItem]:
    """Publications in a verification status (default `pending`), oldest first."""
    return service.list_publication_queue(query)


@router.get("/verifications/evidence")
def list_evidence_verification_queue(
    query: Annotated[VerificationQueueQuery, Query()], service: VerificationServiceDep
) -> PageResponse[EvidenceQueueItem]:
    """Uploaded evidence files in a verification status (default `pending`), oldest first."""
    return service.list_evidence_queue(query)
