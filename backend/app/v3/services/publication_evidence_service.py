"""Evidence files of a publication that is not tied to any workload entry (V4 FR4),
stored in S3 the same way as app/v3/services/evidence_service.py. Files never pass
through the API: the server only hands out short-lived presigned URLs.

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
    ForbiddenError,
    NotFoundError,
    PreconditionFailedError,
    UnauthorizedError,
)
from app.v2.models.enums import EvidenceStatus, VerificationStatus
from app.v2.models.publication import Publication, PublicationEvidence
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.publication_evidence_dao import PublicationEvidenceDAO
from app.v3.dtos.common import ListMeta, ListResponse
from app.v3.dtos.publication_evidence_dto import (
    PublicationEvidenceCreateRequest,
    PublicationEvidenceResponse,
    PublicationEvidenceUpdateRequest,
    PublicationEvidenceUploadResponse,
    publication_evidence_etag,
)
from app.v3.security import Actor, Role
from app.v3.storage.object_storage import ObjectStorage, PresignedDownload

_SAFE_EXTENSION = re.compile(r"^\.[a-z0-9]{1,10}$")


class PublicationEvidenceService:
    def __init__(
        self,
        evidence_dao: PublicationEvidenceDAO,
        publication_dao: PublicationDAO,
        storage: ObjectStorage,
        settings: Settings,
    ) -> None:
        self.evidence_dao = evidence_dao
        self.publication_dao = publication_dao
        self.storage = storage
        self.settings = settings

    def list_evidence(self, publication_id: int) -> ListResponse[PublicationEvidenceResponse]:
        self._require_publication(publication_id)
        items = [
            PublicationEvidenceResponse.model_validate(evidence)
            for evidence in self.evidence_dao.list_by_publication(publication_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_evidence(
        self, publication_id: int, actor: Actor, data: PublicationEvidenceCreateRequest
    ) -> PublicationEvidenceUploadResponse:
        publication = self._require_publication(publication_id)
        self._require_editable(publication_id, publication, actor)
        if actor.lecturer_id is None:
            raise UnauthorizedError("Sign in as a person: evidence records who uploaded it")
        if data.mime_type not in self.settings.evidence_allowed_mime_types:
            allowed = ", ".join(self.settings.evidence_allowed_mime_types)
            raise BadRequestError(f"mime_type must be one of: {allowed}")
        if data.size_bytes > self.settings.evidence_max_bytes:
            raise BadRequestError(f"File is larger than {self.settings.evidence_max_bytes} bytes")

        extension = PurePath(data.file_name).suffix.lower()
        if not _SAFE_EXTENSION.match(extension):
            extension = ""
        key = f"publications/{publication_id}/{uuid4().hex}{extension}"
        evidence = self.evidence_dao.add(
            PublicationEvidence(
                publication_id=publication_id,
                s3_key=key,
                uploaded_by=actor.lecturer_id,
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
        return PublicationEvidenceUploadResponse(
            evidence=PublicationEvidenceResponse.model_validate(evidence),
            upload_url=upload.url,
            fields=upload.fields,
            expires_at=upload.expires_at,
        )

    def update_evidence(
        self,
        publication_id: int,
        evidence_id: UUID,
        actor: Actor,
        data: PublicationEvidenceUpdateRequest,
        if_match: str | None,
    ) -> PublicationEvidenceResponse:
        publication = self._require_publication(publication_id)
        evidence = self._require_evidence(publication_id, evidence_id)
        if if_match is not None and if_match != publication_evidence_etag(
            PublicationEvidenceResponse.model_validate(evidence)
        ):
            raise PreconditionFailedError("The evidence was changed by someone else; reload it")
        self._require_editable(publication_id, publication, actor)

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
        return PublicationEvidenceResponse.model_validate(
            self.evidence_dao.update(evidence, values)
        )

    def get_download(self, publication_id: int, evidence_id: UUID) -> PresignedDownload:
        self._require_publication(publication_id)
        evidence = self._require_evidence(publication_id, evidence_id)
        if evidence.status is not EvidenceStatus.UPLOADED:
            raise ConflictError("The file has not been uploaded yet")
        return self.storage.create_presigned_download(
            key=evidence.s3_key,
            file_name=evidence.file_name,
            expires_in_seconds=self.settings.s3_presign_expires_seconds,
        )

    def delete_evidence(self, publication_id: int, evidence_id: UUID, actor: Actor) -> None:
        publication = self._require_publication(publication_id)
        evidence = self._require_evidence(publication_id, evidence_id)
        self._require_editable(publication_id, publication, actor)
        key = evidence.s3_key
        self.evidence_dao.delete(evidence)
        self.storage.delete_object(key)

    # --- helpers ------------------------------------------------------------------

    def _require_publication(self, publication_id: int) -> Publication:
        publication = self.publication_dao.get_by_id(publication_id)
        if publication is None:
            raise NotFoundError("Publication not found")
        return publication

    def _require_evidence(self, publication_id: int, evidence_id: UUID) -> PublicationEvidence:
        evidence = self.evidence_dao.get_by_id(evidence_id)
        if evidence is None or evidence.publication_id != publication_id:
            raise NotFoundError("Evidence not found")
        return evidence

    def _require_editable(
        self, publication_id: int, publication: Publication, actor: Actor
    ) -> None:
        """Same rule as changing the publication itself (PublicationService):
        its authors or staff, and not once a reviewer has verified it."""
        if not actor.has_any(Role.STAFF):
            if actor.lecturer_id not in self.publication_dao.get_author_ids(publication_id):
                raise ForbiddenError("Only its authors or staff can attach evidence")
            if publication.verification_status is VerificationStatus.VERIFIED:
                raise ForbiddenError("This publication is verified; ask staff to change it")
