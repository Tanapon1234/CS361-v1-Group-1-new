"""Reviewers verify or reject publications and evidence files (docs/v2/permissions.md).

Nobody verifies their own work. A verified publication is locked for its authors
(PublicationService); an author's edit of a rejected one sends it back to `pending`.
"""

from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.v2.models.enums import EvidenceStatus, VerificationStatus
from app.v2.models.publication import Publication
from app.v2.models.submission import EntryEvidence, Submission
from app.v3.daos.evidence_dao import EvidenceDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.daos.verification_dao import VerificationDAO
from app.v3.dtos.common import PageMeta, PageResponse
from app.v3.dtos.verification_dto import (
    EvidenceQueueItem,
    PublicationQueueItem,
    VerificationPutRequest,
    VerificationQueueQuery,
    VerificationResponse,
)
from app.v3.security import Actor
from app.v3.services.access import require_view_submission


class VerificationService:
    def __init__(
        self,
        verification_dao: VerificationDAO,
        publication_dao: PublicationDAO,
        evidence_dao: EvidenceDAO,
        submission_dao: SubmissionDAO,
    ) -> None:
        self.verification_dao = verification_dao
        self.publication_dao = publication_dao
        self.evidence_dao = evidence_dao
        self.submission_dao = submission_dao

    # --- publications -------------------------------------------------------------

    def get_publication_verification(self, publication_id: int) -> VerificationResponse:
        return VerificationResponse.model_validate(self._require_publication(publication_id))

    def set_publication_verification(
        self, publication_id: int, actor: Actor, data: VerificationPutRequest
    ) -> VerificationResponse:
        publication = self._require_publication(publication_id)
        reviewer = self._reviewer_id(actor)
        if reviewer in self.publication_dao.get_author_ids(publication_id):
            raise ForbiddenError("You cannot verify your own publication")
        updated = self.publication_dao.update(publication, self._verdict(reviewer, data))
        return VerificationResponse.model_validate(updated)

    def list_publication_queue(
        self, query: VerificationQueueQuery
    ) -> PageResponse[PublicationQueueItem]:
        items, total = self.verification_dao.find_publications(
            query.status, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[
                PublicationQueueItem(
                    **publication.model_dump(
                        include={
                            "publication_id",
                            "title",
                            "publication_year",
                            "venue",
                            "doi",
                            "verification_status",
                            "verification_note",
                            "created_at",
                        }
                    ),
                    authors=self.verification_dao.author_names(publication.publication_id),
                )
                for publication in items
            ],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    # --- evidence -----------------------------------------------------------------

    def get_evidence_verification(self, evidence_id: UUID, actor: Actor) -> VerificationResponse:
        evidence, submission = self._require_evidence(evidence_id)
        require_view_submission(actor, submission)
        return VerificationResponse.model_validate(evidence)

    def set_evidence_verification(
        self, evidence_id: UUID, actor: Actor, data: VerificationPutRequest
    ) -> VerificationResponse:
        evidence, submission = self._require_evidence(evidence_id)
        reviewer = self._reviewer_id(actor)
        if submission.lecturer_id == reviewer:
            raise ForbiddenError("You cannot verify evidence of your own submission")
        if evidence.status is not EvidenceStatus.UPLOADED:
            raise ConflictError("The file has not been uploaded yet")
        updated = self.evidence_dao.update(evidence, self._verdict(reviewer, data))
        return VerificationResponse.model_validate(updated)

    def list_evidence_queue(self, query: VerificationQueueQuery) -> PageResponse[EvidenceQueueItem]:
        rows, total = self.verification_dao.find_evidence(
            query.status, limit=query.limit, offset=query.offset
        )
        return PageResponse(
            items=[
                EvidenceQueueItem(
                    evidence_id=row.evidence.id,
                    file_name=row.evidence.file_name,
                    label=row.evidence.label,
                    entry_id=row.entry.id,
                    entry_title=row.entry.title,
                    submission_id=row.submission.id,
                    owner_id=row.owner.lecturer_id,
                    owner_name_th=row.owner.name_th,
                    verification_status=row.evidence.verification_status,
                    verification_note=row.evidence.verification_note,
                    created_at=row.evidence.created_at,
                )
                for row in rows
            ],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    # --- helpers ------------------------------------------------------------------

    @staticmethod
    def _reviewer_id(actor: Actor) -> UUID:
        if actor.lecturer_id is None:
            raise UnauthorizedError("Sign in as a person: a verification is signed")
        return actor.lecturer_id

    @staticmethod
    def _verdict(reviewer: UUID, data: VerificationPutRequest) -> dict[str, object]:
        pending = data.status is VerificationStatus.PENDING
        return {
            "verification_status": data.status,
            "verification_note": data.note,
            "verified_by": None if pending else reviewer,
            "verified_at": None if pending else datetime.now(UTC),
        }

    def _require_publication(self, publication_id: int) -> Publication:
        publication = self.publication_dao.get_by_id(publication_id)
        if publication is None:
            raise NotFoundError("Publication not found")
        return publication

    def _require_evidence(self, evidence_id: UUID) -> tuple[EntryEvidence, Submission]:
        evidence = self.evidence_dao.get_by_id(evidence_id)
        if evidence is None:
            raise NotFoundError("Evidence not found")
        entry = self.submission_dao.get_entry(evidence.entry_id)
        submission = self.submission_dao.get_by_id(entry.submission_id) if entry else None
        if submission is None:
            raise NotFoundError("Submission not found")
        return evidence, submission
