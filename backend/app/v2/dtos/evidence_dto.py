"""Evidence files of an entry. Files never pass through the API:

1. `POST /entries/{entry_id}/evidence` -> a `pending` row + a presigned S3 upload
2. the client uploads straight to S3
3. `PATCH /evidence/{evidence_id}` with `{"status": "uploaded", ...}` -> the server checks S3
4. `GET /evidence/{evidence_id}/content` -> 302 to a presigned download URL
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.models.enums import EvidenceStatus


class EvidenceCreateRequest(RequestDTO):
    file_name: str = Field(min_length=1, max_length=255, examples=["order-112.pdf"])
    mime_type: str = Field(min_length=1, max_length=100, examples=["application/pdf"])
    size_bytes: int = Field(gt=0)
    label: str | None = Field(default=None, max_length=255, examples=["คำสั่งแต่งตั้ง"])
    ref_code: str | None = Field(default=None, max_length=50)


class EvidenceUpdateRequest(RequestDTO):
    """Confirm the upload (`status: uploaded`) and/or change the label."""

    status: EvidenceStatus | None = None
    checksum: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$", description="SHA-256, lowercase hex"
    )
    size_bytes: int | None = Field(default=None, gt=0)
    label: str | None = Field(default=None, max_length=255)
    ref_code: str | None = Field(default=None, max_length=50)


class EvidenceResponse(ResponseDTO):
    id: UUID
    entry_id: UUID
    ref_code: str | None
    label: str | None
    file_name: str
    mime_type: str
    size_bytes: int
    checksum: str | None
    status: EvidenceStatus
    uploaded_by: UUID
    created_at: datetime


def evidence_etag(evidence: EvidenceResponse) -> str:
    return f'"{evidence.id}-{evidence.status}-{evidence.size_bytes}-{evidence.checksum or ""}"'


class EvidenceUploadResponse(BaseModel):
    evidence: EvidenceResponse
    upload_url: str
    # Form fields of the presigned POST; send them with the file
    fields: dict[str, str]
    expires_at: datetime
