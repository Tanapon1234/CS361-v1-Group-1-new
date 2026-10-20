"""A reviewer's verdict on a publication or an evidence file, and the review queues."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import PageQuery
from app.v2.models.enums import VerificationStatus


class VerificationPutRequest(RequestDTO):
    status: VerificationStatus
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def rejection_needs_a_reason(self) -> Self:
        if self.status is VerificationStatus.REJECTED and not self.note:
            raise ValueError("Say why it is rejected (note)")
        return self


class VerificationResponse(ResponseDTO):
    verification_status: VerificationStatus
    verification_note: str | None
    verified_by: UUID | None
    verified_at: datetime | None


class VerificationQueueQuery(PageQuery):
    status: VerificationStatus = VerificationStatus.PENDING


class PublicationQueueItem(ResponseDTO):
    publication_id: int
    title: str
    publication_year: int | None
    venue: str | None
    doi: str | None
    authors: list[str]
    verification_status: VerificationStatus
    verification_note: str | None
    created_at: datetime | None


class EvidenceQueueItem(ResponseDTO):
    evidence_id: UUID
    file_name: str
    label: str | None
    entry_id: UUID
    entry_title: str | None
    submission_id: UUID
    owner_id: UUID
    owner_name_th: str
    verification_status: VerificationStatus
    verification_note: str | None
    created_at: datetime
