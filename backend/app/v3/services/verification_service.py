"""Reviewers verify or reject publications and evidence files (docs/v2/permissions.md).

Nobody verifies their own work. A verified publication is locked for its authors
(PublicationService); an author's edit of a rejected one sends it back to `pending`.
"""

from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.v2.models.enums import EvidenceStatus, SubmissionStatus, VerificationStatus
from app.v2.models.publication import Publication
from app.v2.models.submission import EntryEvidence, Submission
from app.v2.models.submission_review import SubmissionReview
from app.v3.daos.evidence_dao import EvidenceDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.daos.submission_review_dao import SubmissionReviewDAO
from app.v3.daos.verification_dao import VerificationDAO
from app.v3.dtos.common import PageMeta, PageResponse
from app.v3.dtos.verification_dto import (
    EvidenceQueueItem,
    PublicationQueueItem,
    ReviewAssignmentItem,
    SubmissionReviewResponse,
    VerificationPutRequest,
    VerificationQueueQuery,
    VerificationResponse,
)
from app.v3.security import Actor, Role
from app.v3.services.access import require_view_submission


class VerificationService:
    def __init__(
        self,
        verification_dao: VerificationDAO,
        publication_dao: PublicationDAO,
        evidence_dao: EvidenceDAO,
        submission_dao: SubmissionDAO,
        assignment_dao: ReviewerAssignmentDAO,
        review_dao: SubmissionReviewDAO,
        lecturer_dao: LecturerDAO,
    ) -> None:
        self.verification_dao = verification_dao
        self.publication_dao = publication_dao
        self.evidence_dao = evidence_dao
        self.submission_dao = submission_dao
        self.assignment_dao = assignment_dao
        self.review_dao = review_dao
        self.lecturer_dao = lecturer_dao

    # --- publications -------------------------------------------------------------

    def get_publication_verification(self, publication_id: int) -> VerificationResponse:
        return VerificationResponse.model_validate(self._require_publication(publication_id))

    def set_publication_verification(
        self, publication_id: int, actor: Actor, data: VerificationPutRequest
    ) -> VerificationResponse:
        publication = self._require_publication(publication_id)
        reviewer = self._require_reviewer(actor)
        authors = self.publication_dao.get_author_ids(publication_id)
        if reviewer in authors:
            raise ForbiddenError("You cannot verify your own publication")
        if not set(authors) & set(self.assignment_dao.reviewee_ids(reviewer)):
            raise ForbiddenError("You are not assigned to review any author of this publication")
        updated = self.publication_dao.update(publication, self._verdict(reviewer, data))
        return VerificationResponse.model_validate(updated)

    def list_publication_queue(
        self, actor: Actor, query: VerificationQueueQuery
    ) -> PageResponse[PublicationQueueItem]:
        items, total = self.verification_dao.find_publications(
            query.status,
            limit=query.limit,
            offset=query.offset,
            reviewee_ids=self._reviewee_scope(actor),
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
        reviewer = self._require_reviewer(actor)
        if submission.lecturer_id == reviewer:
            raise ForbiddenError("You cannot verify evidence of your own submission")
        if not self.assignment_dao.is_assigned(
            reviewer, submission.lecturer_id, submission.round_id
        ):
            raise ForbiddenError("You are not assigned to review this lecturer in this round")
        if evidence.status is not EvidenceStatus.UPLOADED:
            raise ConflictError("The file has not been uploaded yet")
        updated = self.evidence_dao.update(evidence, self._verdict(reviewer, data))
        return VerificationResponse.model_validate(updated)

    def list_evidence_queue(
        self, actor: Actor, query: VerificationQueueQuery
    ) -> PageResponse[EvidenceQueueItem]:
        rows, total = self.verification_dao.find_evidence(
            query.status,
            limit=query.limit,
            offset=query.offset,
            reviewee_ids=self._reviewee_scope(actor),
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

    # --- whole sheets (V4 #335) -----------------------------------------------------

    def get_submission_review(self, submission_id: UUID, actor: Actor) -> SubmissionReviewResponse:
        submission = self._require_submission(submission_id)
        require_view_submission(actor, submission)
        review = self.review_dao.get(submission_id)
        if review is None:
            return SubmissionReviewResponse(
                status=VerificationStatus.PENDING, note=None, reviewed_by=None, reviewed_at=None
            )
        return SubmissionReviewResponse.model_validate(review, from_attributes=True)

    def set_submission_review(
        self, submission_id: UUID, actor: Actor, data: VerificationPutRequest
    ) -> SubmissionReviewResponse:
        """The assigned reviewer's verdict on a submitted sheet. It never changes the sheet's
        workflow status; the lecturer and the approvers see the verdict and its note."""
        submission = self._require_submission(submission_id)
        reviewer = self._require_reviewer(actor)
        if submission.lecturer_id == reviewer:
            raise ForbiddenError("You cannot review your own submission")
        if not self.assignment_dao.is_assigned(
            reviewer, submission.lecturer_id, submission.round_id
        ):
            raise ForbiddenError("You are not assigned to review this lecturer in this round")
        if submission.status is SubmissionStatus.DRAFT:
            raise ConflictError("The sheet has not been submitted yet")
        verdict = self._verdict(reviewer, data)
        values = {
            "status": data.status,
            "note": data.note,
            "reviewed_by": verdict["verified_by"],
            "reviewed_at": verdict["verified_at"],
        }
        review = self.review_dao.get(submission_id)
        if review is None:
            review = self.review_dao.add(SubmissionReview(submission_id=submission_id, **values))
        else:
            review = self.review_dao.update(review, values)
        return SubmissionReviewResponse.model_validate(review, from_attributes=True)

    def list_assignments(self, actor: Actor) -> list[ReviewAssignmentItem]:
        """What the caller reviews now: every active assignment, newest round first, with the
        sheet (if the lecturer has made one), its verdict, and what is still pending."""
        reviewer = self._require_reviewer(actor)
        assignments = self.assignment_dao.list_by_reviewer(reviewer)
        items: list[ReviewAssignmentItem] = []
        for assignment in assignments:
            lecturer = self.lecturer_dao.get_by_id(assignment.reviewee_id)
            sheet = self.submission_dao.get_by_round_and_lecturer(
                assignment.round_id, assignment.reviewee_id
            )
            review = self.review_dao.get(sheet.id) if sheet else None
            items.append(
                ReviewAssignmentItem(
                    round_id=assignment.round_id,
                    reviewee_id=assignment.reviewee_id,
                    reviewee_name_th=lecturer.name_th if lecturer else "-",
                    submission_id=sheet.id if sheet else None,
                    submission_status=sheet.status if sheet else None,
                    review_status=(review.status if review else VerificationStatus.PENDING)
                    if sheet
                    else None,
                    review_note=review.note if review else None,
                    pending_evidence=(
                        self.verification_dao.count_pending_evidence(sheet.id) if sheet else 0
                    ),
                    pending_publications=self.verification_dao.count_pending_publications(
                        assignment.reviewee_id
                    ),
                )
            )
        items.sort(key=lambda item: (-item.round_id, item.reviewee_name_th))
        return items

    # --- helpers ------------------------------------------------------------------

    def _require_submission(self, submission_id: UUID) -> Submission:
        submission = self.submission_dao.get_by_id(submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        return submission

    def _reviewee_scope(self, actor: Actor) -> list[UUID]:
        """The lecturers this reviewer is assigned to right now (open rounds only). Nobody
        else sees the queue: staff, executives and admins may read sheets but do not verify."""
        return list(self.assignment_dao.reviewee_ids(self._require_reviewer(actor)))

    @staticmethod
    def _require_reviewer(actor: Actor) -> UUID:
        """The signed-in lecturer, who must hold the `reviewer` role itself: admin counts as
        every role elsewhere (Actor.has_any) but cannot verify unless assigned."""
        if actor.lecturer_id is None:
            raise UnauthorizedError("Sign in as a person: a verification is signed")
        if Role.REVIEWER not in actor.roles:
            raise ForbiddenError("Only a reviewer assigned to this lecturer can verify")
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
