"""Evidence files of an entry, stored in S3. Files never pass through the API: the server
only hands out short-lived presigned URLs (see app/v2/dtos/evidence_dto.py for the flow).

Rows that stay `pending` (URL issued, upload never finished) should be swept by a job
later; that job is not part of the API.
"""

import re
from pathlib import PurePath
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    PreconditionFailedError,
    UnauthorizedError,
)
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.evidence_dto import (
    EvidenceCreateRequest,
    EvidenceResponse,
    EvidenceUpdateRequest,
    EvidenceUploadResponse,
    evidence_etag,
)
from app.v2.models.enums import EvidenceStatus
from app.v2.models.submission import EntryEvidence, Submission, SubmissionEntry
from app.v2.services.workflow import EDITABLE_STATUSES
from app.v2.storage.object_storage import ObjectStorage, PresignedDownload

_SAFE_EXTENSION = re.compile(r"^\.[a-z0-9]{1,10}$")


class EvidenceService:
    def __init__(
        self,
        evidence_dao: EvidenceDAO,
        submission_dao: SubmissionDAO,
        lecturer_dao: LecturerDAO,
        storage: ObjectStorage,
        settings: Settings,
    ) -> None:
        self.evidence_dao = evidence_dao
        self.submission_dao = submission_dao
        self.lecturer_dao = lecturer_dao
        self.storage = storage
        self.settings = settings

    def list_evidence(self, entry_id: UUID) -> ListResponse[EvidenceResponse]:
        self._require_entry(entry_id)
        items = [
            EvidenceResponse.model_validate(evidence)
            for evidence in self.evidence_dao.list_by_entry(entry_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_evidence(
        self, entry_id: UUID, actor_id: UUID, data: EvidenceCreateRequest
    ) -> EvidenceUploadResponse:
        entry = self._require_entry(entry_id)
        self._require_editable(entry, actor_id)
        if data.mime_type not in self.settings.evidence_allowed_mime_types:
            allowed = ", ".join(self.settings.evidence_allowed_mime_types)
            raise BadRequestError(f"mime_type must be one of: {allowed}")
        if data.size_bytes > self.settings.evidence_max_bytes:
            raise BadRequestError(f"File is larger than {self.settings.evidence_max_bytes} bytes")

        extension = PurePath(data.file_name).suffix.lower()
        if not _SAFE_EXTENSION.match(extension):
            extension = ""
        key = f"submissions/{entry.submission_id}/entries/{entry_id}/{uuid4().hex}{extension}"
        evidence = self.evidence_dao.add(
            EntryEvidence(
                entry_id=entry_id,
                s3_key=key,
                uploaded_by=actor_id,
                status=EvidenceStatus.PENDING,
                **data.model_dump(),
            )
        )
        upload = self.storage.create_presigned_upload(
            key=key,
            content_type=data.mime_type,
            max_size_bytes=data.size_bytes,
            expires_in_seconds=self.settings.s3_presign_expires_seconds,
        )
        return EvidenceUploadResponse(
            evidence=EvidenceResponse.model_validate(evidence),
            upload_url=upload.url,
            fields=upload.fields,
            expires_at=upload.expires_at,
        )

    def get_evidence(self, evidence_id: UUID) -> EvidenceResponse:
        return EvidenceResponse.model_validate(self._require_evidence(evidence_id))

    def update_evidence(
        self, evidence_id: UUID, actor_id: UUID, data: EvidenceUpdateRequest, if_match: str | None
    ) -> EvidenceResponse:
        evidence = self._require_evidence(evidence_id)
        if if_match is not None and if_match != evidence_etag(
            EvidenceResponse.model_validate(evidence)
        ):
            raise PreconditionFailedError("The evidence was changed by someone else; reload it")
        self._require_editable(self._require_entry(evidence.entry_id), actor_id)

        values = data.model_dump(exclude_unset=True)
        if "status" in values:
            if values["status"] is not EvidenceStatus.UPLOADED:
                raise BadRequestError("status can only be set to uploaded")
            stored = self.storage.head_object(evidence.s3_key)
            if stored is None:
                raise BadRequestError("The file is not in storage yet; upload it first")
            if "size_bytes" in values and values["size_bytes"] != stored.size_bytes:
                raise BadRequestError(
                    f"size_bytes {values['size_bytes']} does not match the uploaded file "
                    f"({stored.size_bytes})"
                )
            values["size_bytes"] = stored.size_bytes
        elif "size_bytes" in values:
            raise BadRequestError("size_bytes is set when confirming the upload")
        return EvidenceResponse.model_validate(self.evidence_dao.update(evidence, values))

    def get_download(self, evidence_id: UUID) -> PresignedDownload:
        evidence = self._require_evidence(evidence_id)
        # TODO(auth): only people who may see the submission
        if evidence.status is not EvidenceStatus.UPLOADED:
            raise ConflictError("The file has not been uploaded yet")
        return self.storage.create_presigned_download(
            key=evidence.s3_key,
            file_name=evidence.file_name,
            expires_in_seconds=self.settings.s3_presign_expires_seconds,
        )

    def delete_evidence(self, evidence_id: UUID, actor_id: UUID) -> None:
        evidence = self._require_evidence(evidence_id)
        self._require_editable(self._require_entry(evidence.entry_id), actor_id)
        key = evidence.s3_key
        self.evidence_dao.delete(evidence)
        self.storage.delete_object(key)

    # --- helpers ------------------------------------------------------------------

    def _require_entry(self, entry_id: UUID) -> SubmissionEntry:
        entry = self.submission_dao.get_entry(entry_id)
        if entry is None:
            raise NotFoundError("Entry not found")
        return entry

    def _require_evidence(self, evidence_id: UUID) -> EntryEvidence:
        evidence = self.evidence_dao.get_by_id(evidence_id)
        if evidence is None:
            raise NotFoundError("Evidence not found")
        return evidence

    def _require_editable(self, entry: SubmissionEntry, actor_id: UUID) -> Submission:
        actor = self.lecturer_dao.get_by_id(actor_id)
        if actor is None or not actor.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")
        submission = self.submission_dao.get_by_id(entry.submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        # TODO(auth): only the owner (submission.lecturer_id == actor_id)
        if submission.status not in EDITABLE_STATUSES:
            raise ConflictError(f"The submission is {submission.status} and can no longer change")
        return submission
