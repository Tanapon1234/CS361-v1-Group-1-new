"""Evidence files of a publication that is not tied to any workload entry (V4 FR4).
Same presigned-S3 flow as app/v3/dtos/evidence_dto.py:

1. `POST /publications/{publication_id}/evidence` -> a `pending` row + a presigned S3 upload
2. the client uploads straight to S3
3. `PATCH /publications/{publication_id}/evidence/{evidence_id}` with `{"status": "uploaded"}`
   -> the server checks S3
4. `GET /publications/{publication_id}/evidence/{evidence_id}/content` -> 302 to a download URL

No per-file verification: the publication's own verification_status (005) covers it.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.v2.models.enums import EvidenceStatus
from app.v3.dtos.base import RequestDTO, ResponseDTO


class PublicationEvidenceCreateRequest(RequestDTO):
    file_name: str = Field(min_length=1, max_length=255, examples=["reprint.pdf"])
    mime_type: str = Field(min_length=1, max_length=100, examples=["application/pdf"])
    size_bytes: int = Field(gt=0)
    label: str | None = Field(default=None, max_length=255, examples=["ฉบับตีพิมพ์"])


class PublicationEvidenceUpdateRequest(RequestDTO):
    """Confirm the upload (`status: uploaded`) and/or change the label."""

    status: EvidenceStatus | None = None
    checksum: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$", description="SHA-256, lowercase hex"
    )
    size_bytes: int | None = Field(default=None, gt=0)
    label: str | None = Field(default=None, max_length=255)


class PublicationEvidenceResponse(ResponseDTO):
    id: UUID
    publication_id: int
    label: str | None
    file_name: str
    mime_type: str
    size_bytes: int
    checksum: str | None
    status: EvidenceStatus
    uploaded_by: UUID
    created_at: datetime


def publication_evidence_etag(evidence: PublicationEvidenceResponse) -> str:
    return f'"{evidence.id}-{evidence.status}-{evidence.size_bytes}-{evidence.checksum or ""}"'


class PublicationEvidenceUploadResponse(BaseModel):
    evidence: PublicationEvidenceResponse
    upload_url: str
    fields: dict[str, str]
    expires_at: datetime
