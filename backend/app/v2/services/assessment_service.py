"""Values that position holders give to ranged items (e.g. 3.1 / 3.2 administrative work).

An assessor may give one value per entry, only while the submission is `assessing`, and
only for items whose `assessor_position` they hold (a department-level position only
covers its own department). Each change re-scores the entry and the submission.
"""

from datetime import UTC, date, datetime
from uuid import UUID

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.v2.daos.assessment_dao import AssessmentDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.assessment_dto import (
    AssessmentPutRequest,
    AssessmentQueueItem,
    AssessmentQueueQuery,
    AssessmentResponse,
)
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.submission_dto import EntryResponse
from app.v2.models.enums import AssessmentAgg, SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.member_position import MemberPosition
from app.v2.models.rubric import RubricItem
from app.v2.models.submission import EntryAssessment, Submission, SubmissionEntry
from app.v2.services.score_keeper import ScoreKeeper
from app.v2.services.scoring import needs_assessment, validate_assessment_value


class AssessmentService:
    def __init__(
        self,
        assessment_dao: AssessmentDAO,
        submission_dao: SubmissionDAO,
        position_dao: MemberPositionDAO,
        lecturer_dao: LecturerDAO,
        score_keeper: ScoreKeeper,
    ) -> None:
        self.assessment_dao = assessment_dao
        self.submission_dao = submission_dao
        self.position_dao = position_dao
        self.lecturer_dao = lecturer_dao
        self.score_keeper = score_keeper

    def list_queue(
        self, actor_id: UUID, query: AssessmentQueueQuery
    ) -> PageResponse[AssessmentQueueItem]:
        """The caller's to-do list: entries their current positions may assess."""
        self._require_actor(actor_id)
        positions = self.position_dao.list_active(actor_id, date.today())
        rows, total = self.assessment_dao.find_queue(
            assessor_id=actor_id,
            positions=positions,
            round_id=query.round_id,
            assessed=None if query.status is None else query.status == "done",
            limit=query.limit,
            offset=query.offset,
        )
        items = [
            AssessmentQueueItem(
                entry=EntryResponse.model_validate(entry),
                lecturer_id=lecturer.lecturer_id,
                lecturer_name_th=lecturer.name_th,
                department_id=submission.department_snapshot,
                item_label_th=item.label_th,
                assessor_position=item.assessor_position,
                range_basis=item.range_basis,
                weight_min=item.weight_min,
                weight_max=item.weight_max,
                my_assessment=AssessmentResponse.model_validate(mine) if mine else None,
            )
            for entry, submission, item, lecturer, mine in rows
        ]
        return PageResponse(
            items=items, meta=PageMeta(total=total, limit=query.limit, offset=query.offset)
        )

    def list_entry_assessments(self, entry_id: UUID) -> ListResponse[AssessmentResponse]:
        self._require_entry(entry_id)
        # TODO(auth): assessors of this entry and admins only
        items = [
            AssessmentResponse.model_validate(assessment)
            for assessment in self.assessment_dao.list_by_entry(entry_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def put_my_assessment(
        self, entry_id: UUID, actor_id: UUID, data: AssessmentPutRequest
    ) -> AssessmentResponse:
        """Give or change the caller's value (idempotent: the same body gives the same result)."""
        self._require_actor(actor_id)
        entry = self._require_entry(entry_id)
        submission, item = self._require_assessable(entry)
        if submission.lecturer_id == actor_id:
            raise ForbiddenError("You cannot assess your own submission")
        position = self._position_for(actor_id, item, submission)

        error = validate_assessment_value(item, data.value_given)
        if error:
            raise BadRequestError(error)

        mine = self.assessment_dao.get_by_entry_and_assessor(entry_id, actor_id)
        values = {
            "position_used": position.position,
            "value_given": data.value_given,
            "comment": data.comment,
            "assessed_at": datetime.now(UTC),
        }
        if mine is not None:
            mine = self.assessment_dao.update(mine, values)
        else:
            if item.assessment_agg is AssessmentAgg.SINGLE and self.assessment_dao.list_by_entry(
                entry_id
            ):
                raise ConflictError("This item takes one assessor and already has a value")
            mine = self.assessment_dao.add(
                EntryAssessment(entry_id=entry_id, assessor_id=actor_id, **values)
            )
        self._rescore(entry, submission)
        return AssessmentResponse.model_validate(mine)

    def delete_my_assessment(self, entry_id: UUID, actor_id: UUID) -> None:
        self._require_actor(actor_id)
        entry = self._require_entry(entry_id)
        submission, _ = self._require_assessable(entry)
        mine = self.assessment_dao.get_by_entry_and_assessor(entry_id, actor_id)
        if mine is None:
            raise NotFoundError("You have not assessed this entry")
        self.assessment_dao.delete(mine)
        self._rescore(entry, submission)

    # --- helpers ------------------------------------------------------------------

    def _require_actor(self, actor_id: UUID) -> Lecturer:
        lecturer = self.lecturer_dao.get_by_id(actor_id)
        if lecturer is None or not lecturer.is_active:
            raise UnauthorizedError("Unknown or inactive lecturer")
        return lecturer

    def _require_entry(self, entry_id: UUID) -> SubmissionEntry:
        entry = self.submission_dao.get_entry(entry_id)
        if entry is None:
            raise NotFoundError("Entry not found")
        return entry

    def _require_assessable(self, entry: SubmissionEntry) -> tuple[Submission, RubricItem]:
        submission = self.submission_dao.get_by_id(entry.submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        item = self.score_keeper.rubric_of(submission).items[entry.item_id]
        if not needs_assessment(item):
            raise BadRequestError("This entry's item has a fixed weight; nobody assesses it")
        if submission.status is not SubmissionStatus.ASSESSING:
            raise ConflictError(f"The submission is {submission.status}, not assessing")
        return submission, item

    def _position_for(
        self, actor_id: UUID, item: RubricItem, submission: Submission
    ) -> MemberPosition:
        for position in self.position_dao.list_active(actor_id, date.today()):
            if position.position == item.assessor_position and position.department_id in (
                None,
                submission.department_snapshot,
            ):
                return position
        raise ForbiddenError(f"Only a current {item.assessor_position} can assess this item")

    def _rescore(self, entry: SubmissionEntry, submission: Submission) -> None:
        rubric = self.score_keeper.rubric_of(submission)
        self.score_keeper.rescore_entry(entry, rubric)
        self.score_keeper.refresh(submission, rubric, freeze=True)
