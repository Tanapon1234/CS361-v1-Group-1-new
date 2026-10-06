from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import and_, false, func, or_, true
from sqlmodel import col, select

from app.v2.daos.assessment_dao import AssessmentDAO, QueueRow
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.enums import SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.member_position import MemberPosition
from app.v2.models.rubric import RubricItem
from app.v2.models.submission import EntryAssessment, Submission, SubmissionEntry


class SqlAssessmentDAO(SqlDAO, AssessmentDAO):
    def list_by_entry(self, entry_id: UUID) -> Sequence[EntryAssessment]:
        statement = (
            select(EntryAssessment)
            .where(EntryAssessment.entry_id == entry_id)
            .order_by(col(EntryAssessment.assessed_at), col(EntryAssessment.id))
        )
        return self.session.exec(statement).all()

    def list_by_entries(self, entry_ids: Sequence[UUID]) -> Sequence[EntryAssessment]:
        if not entry_ids:
            return []
        statement = (
            select(EntryAssessment)
            .where(col(EntryAssessment.entry_id).in_(entry_ids))
            .order_by(col(EntryAssessment.assessed_at), col(EntryAssessment.id))
        )
        return self.session.exec(statement).all()

    def get_by_entry_and_assessor(
        self, entry_id: UUID, assessor_id: UUID
    ) -> EntryAssessment | None:
        statement = select(EntryAssessment).where(
            EntryAssessment.entry_id == entry_id, EntryAssessment.assessor_id == assessor_id
        )
        return self.session.exec(statement).first()

    def find_queue(
        self,
        *,
        assessor_id: UUID,
        positions: Sequence[MemberPosition],
        round_id: int | None,
        assessed: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[QueueRow], int]:
        covered = [
            and_(
                RubricItem.assessor_position == position.position,
                Submission.department_snapshot == position.department_id
                if position.department_id is not None
                else true(),
            )
            for position in positions
        ]
        statement = (
            select(SubmissionEntry, Submission, RubricItem, Lecturer, EntryAssessment)
            .join(Submission, col(Submission.id) == SubmissionEntry.submission_id)
            .join(RubricItem, col(RubricItem.id) == SubmissionEntry.item_id)
            .join(Lecturer, col(Lecturer.lecturer_id) == Submission.lecturer_id)
            .outerjoin(
                EntryAssessment,
                and_(
                    col(EntryAssessment.entry_id) == SubmissionEntry.id,
                    col(EntryAssessment.assessor_id) == assessor_id,
                ),
            )
            .where(
                Submission.status == SubmissionStatus.ASSESSING,
                col(RubricItem.assessor_position).is_not(None),
                or_(*covered) if covered else false(),
            )
        )
        if round_id is not None:
            statement = statement.where(Submission.round_id == round_id)
        if assessed is True:
            statement = statement.where(col(EntryAssessment.id).is_not(None))
        elif assessed is False:
            statement = statement.where(col(EntryAssessment.id).is_(None))

        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        rows = self.session.exec(
            statement.order_by(col(Lecturer.name_th), col(SubmissionEntry.sort_order))
            .offset(offset)
            .limit(limit)
        ).all()
        return rows, total

    def add(self, assessment: EntryAssessment) -> EntryAssessment:
        return self._add(assessment)

    def update(self, assessment: EntryAssessment, values: Mapping[str, Any]) -> EntryAssessment:
        return self._update(assessment, values)

    def delete(self, assessment: EntryAssessment) -> None:
        self._delete(assessment)
