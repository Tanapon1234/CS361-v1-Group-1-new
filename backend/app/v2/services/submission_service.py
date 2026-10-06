"""Workload submissions (one per lecturer per round), their totals and approval history.

Auth is not wired yet: `actor_id` is the caller (see `CurrentLecturerIdDep`). Checks of
*who may* do something are marked `TODO(auth)`.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, UnauthorizedError
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.submission_dto import (
    ApprovalCreateRequest,
    ApprovalResponse,
    CategoryScore,
    EntryResponse,
    SubmissionCreateRequest,
    SubmissionDetailResponse,
    SubmissionListQuery,
    SubmissionResponse,
    SubmissionSummaryResponse,
    SubmissionTotalsResponse,
)
from app.v2.models.enums import AcademicRank, ApprovalDecision, SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.submission import Submission, SubmissionApproval
from app.v2.services.db_errors import is_unique_violation
from app.v2.services.score_keeper import ScoreKeeper
from app.v2.services.scoring import ZERO
from app.v2.services.workflow import STEPS
from app.v2.storage.object_storage import ObjectStorage

# lecturer.rank is free text; checked in this order ("รองศาสตราจารย์" contains "ศาสตราจารย์")
_RANK_WORDS: list[tuple[AcademicRank, tuple[str, ...]]] = [
    (AcademicRank.ASSOC_PROF, ("รองศาสตราจารย์", "รศ.", "associate professor", "assoc")),
    (AcademicRank.ASST_PROF, ("ผู้ช่วยศาสตราจารย์", "ผศ.", "assistant professor", "asst")),
    (AcademicRank.PROF, ("ศาสตราจารย์", "ศ.", "professor", "prof")),
    (AcademicRank.LECTURER, ("อาจารย์", "อ.", "lecturer")),
]


def rank_from_text(rank: str | None) -> AcademicRank:
    """Map the free-text `lecturer.rank` to the `academic_rank` enum (empty = lecturer)."""
    if rank is None or not rank.strip():
        return AcademicRank.LECTURER
    text = rank.strip().lower()
    if text in AcademicRank._value2member_map_:
        return AcademicRank(text)
    for academic_rank, words in _RANK_WORDS:
        if any(word in text for word in words):
            return academic_rank
    raise BadRequestError(f"lecturer.rank {rank!r} is not a known academic rank")


class SubmissionService:
    def __init__(
        self,
        submission_dao: SubmissionDAO,
        round_dao: EvaluationRoundDAO,
        lecturer_dao: LecturerDAO,
        evidence_dao: EvidenceDAO,
        storage: ObjectStorage,
        score_keeper: ScoreKeeper,
    ) -> None:
        self.submission_dao = submission_dao
        self.round_dao = round_dao
        self.lecturer_dao = lecturer_dao
        self.evidence_dao = evidence_dao
        self.storage = storage
        self.score_keeper = score_keeper

    # --- submissions --------------------------------------------------------------

    def list_submissions(
        self, actor_id: UUID, query: SubmissionListQuery
    ) -> PageResponse[SubmissionResponse]:
        self._require_actor(actor_id)
        # TODO(auth): limit to what the caller may see (own submissions, or their
        # department's when they hold a position there, or all for the faculty).
        items, total = self.submission_dao.find_page(
            round_id=query.round_id,
            lecturer_id=query.lecturer_id,
            department_id=None,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )
        return PageResponse(
            items=[SubmissionResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_submission(
        self, actor_id: UUID, data: SubmissionCreateRequest
    ) -> SubmissionResponse:
        lecturer = self._require_actor(actor_id)
        evaluation_round = self.round_dao.get_by_id(data.round_id)
        if evaluation_round is None:
            raise BadRequestError("Evaluation round not found")
        if not evaluation_round.is_open:
            raise ConflictError("The evaluation round is not open")
        if lecturer.department_id is None:
            raise BadRequestError("Set the lecturer's department before creating a submission")
        if self.submission_dao.get_by_round_and_lecturer(data.round_id, actor_id) is not None:
            raise ConflictError("You already have a submission in this round")

        submission = Submission(
            round_id=data.round_id,
            lecturer_id=actor_id,
            rank_snapshot=rank_from_text(lecturer.rank),
            department_snapshot=lecturer.department_id,
        )
        try:
            submission = self.submission_dao.add(submission)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("You already have a submission in this round") from exc
            raise
        return SubmissionResponse.model_validate(submission)

    def get_submission(self, submission_id: UUID) -> SubmissionDetailResponse:
        submission = self._require_submission(submission_id)
        entries = self.submission_dao.list_entries(submission_id)
        return SubmissionDetailResponse(
            **SubmissionResponse.model_validate(submission).model_dump(),
            entries=[EntryResponse.model_validate(entry) for entry in entries],
        )

    def delete_submission(self, submission_id: UUID, actor_id: UUID) -> None:
        submission = self._require_submission(submission_id)
        self._require_actor(actor_id)
        # TODO(auth): only the owner (submission.lecturer_id == actor_id)
        if submission.status is not SubmissionStatus.DRAFT:
            raise ConflictError("Only a draft submission can be deleted")
        keys = [evidence.s3_key for evidence in self.evidence_dao.list_by_submission(submission_id)]
        self.submission_dao.delete(submission)
        for key in keys:
            self.storage.delete_object(key)

    def get_summary(self, submission_id: UUID) -> SubmissionSummaryResponse:
        submission = self._require_submission(submission_id)
        rubric = self.score_keeper.rubric_of(submission)
        totals = self.score_keeper.totals(submission, rubric)
        version = rubric.version
        return SubmissionSummaryResponse(
            submission_id=submission.id,
            status=submission.status,
            categories=[
                CategoryScore(
                    category_id=category.id,
                    code=category.code,
                    name_th=category.name_th,
                    cap=category.cap,
                    raw_score=totals.categories.get(category.id, (ZERO, ZERO))[0],
                    capped_score=totals.categories.get(category.id, (ZERO, ZERO))[1],
                )
                for category in rubric.categories
            ],
            raw_total=totals.raw_total,
            capped_total=totals.capped_total,
            overall_cap=version.overall_cap,
            teaching_credits=totals.teaching_credits,
            min_teaching_credits=version.min_teaching_credits,
            min_required=version.min_required,
            meets_min_teaching_credits=totals.teaching_credits >= version.min_teaching_credits,
            meets_min_required=totals.capped_total >= version.min_required,
            pending_assessments=self.score_keeper.pending_assessments(submission.id, rubric),
        )

    def get_totals(self, submission_id: UUID) -> SubmissionTotalsResponse:
        submission = self._require_submission(submission_id)
        frozen = {t.category_id: t for t in self.submission_dao.list_category_totals(submission_id)}
        if not frozen:
            raise ConflictError("The submission has not been sent yet; use /summary")
        rubric = self.score_keeper.rubric_of(submission)
        categories = [
            CategoryScore(
                category_id=category.id,
                code=category.code,
                name_th=category.name_th,
                cap=category.cap,
                raw_score=frozen[category.id].raw_score,
                capped_score=frozen[category.id].capped_score,
            )
            for category in rubric.categories
            if category.id in frozen
        ]
        return SubmissionTotalsResponse(
            submission_id=submission.id,
            status=submission.status,
            submitted_at=submission.submitted_at,
            categories=categories,
            raw_total=sum((c.raw_score for c in categories), ZERO),
            capped_total=min(
                sum((c.capped_score for c in categories), ZERO), rubric.version.overall_cap
            ),
        )

    def get_pdf(self, submission_id: UUID) -> bytes:
        self._require_submission(submission_id)
        # The paper form's layout and a Thai font are not in the repo yet.
        raise NotImplementedError  # TODO: render the official form as PDF

    # --- approvals ----------------------------------------------------------------

    def list_approvals(self, submission_id: UUID) -> ListResponse[ApprovalResponse]:
        self._require_submission(submission_id)
        items = [
            ApprovalResponse.model_validate(approval)
            for approval in self.submission_dao.list_approvals(submission_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_approval(
        self, submission_id: UUID, actor_id: UUID, data: ApprovalCreateRequest
    ) -> ApprovalResponse:
        submission = self._require_submission(submission_id)
        self._require_actor(actor_id)
        step = STEPS.get(submission.status)
        if step is None:
            raise ConflictError(f"A {submission.status} submission cannot change any more")
        # TODO(auth): the caller must be able to sign as `step.role`: the owner for
        # performer; the dept_chair / dept_committee of submission.department_snapshot;
        # faculty staff for receiver.

        changes: dict[str, object] = {}
        if data.decision is ApprovalDecision.RETURNED:
            if not step.can_return:
                raise ConflictError(f"A {submission.status} submission cannot be returned")
            if not data.comment:
                raise BadRequestError("Say why the submission is returned (comment)")
            changes["status"] = SubmissionStatus.RETURNED
        else:
            changes["status"] = step.on_approve
            if submission.status is SubmissionStatus.ASSESSING:
                rubric = self.score_keeper.rubric_of(submission)
                pending = self.score_keeper.pending_assessments(submission.id, rubric)
                if pending:
                    raise ConflictError(f"{pending} entries still wait for an assessor")
            if step.on_approve is SubmissionStatus.SUBMITTED:
                owner = self._require_lecturer(submission.lecturer_id)
                if owner.department_id is None:
                    raise BadRequestError("Set the lecturer's department before sending")
                changes |= {
                    "rank_snapshot": rank_from_text(owner.rank),
                    "department_snapshot": owner.department_id,
                    "submitted_at": datetime.now(UTC),
                }

        approval = self.submission_dao.add(
            SubmissionApproval(
                submission_id=submission.id,
                signer_id=actor_id,
                role=step.role,
                decision=data.decision,
                comment=data.comment,
            )
        )
        submission = self.submission_dao.update(submission, changes)
        if changes["status"] is SubmissionStatus.SUBMITTED:
            rubric = self.score_keeper.rubric_of(submission)
            self.score_keeper.refresh(submission, rubric, freeze=True)
        return ApprovalResponse.model_validate(approval)

    # --- helpers ------------------------------------------------------------------

    def _require_submission(self, submission_id: UUID) -> Submission:
        submission = self.submission_dao.get_by_id(submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        return submission

    def _require_lecturer(self, lecturer_id: UUID) -> Lecturer:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        return lecturer

    def _require_actor(self, actor_id: UUID) -> Lecturer:
        lecturer = self.lecturer_dao.get_by_id(actor_id)
        if lecturer is None or not lecturer.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")
        return lecturer
