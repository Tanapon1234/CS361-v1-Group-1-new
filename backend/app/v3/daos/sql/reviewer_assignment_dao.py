from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import col, select

from app.v2.models.reviewer_assignment import ReviewerAssignment
from app.v2.models.submission import EvaluationRound
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.daos.sql.base import SqlDAO


def _active_round_ids():
    """Rounds still accepting work: open, and not past their submit_due_at (if any)."""
    return select(EvaluationRound.id).where(
        EvaluationRound.is_open.is_(True),
        or_(EvaluationRound.submit_due_at.is_(None), EvaluationRound.submit_due_at > func.now()),
    )


class SqlReviewerAssignmentDAO(SqlDAO, ReviewerAssignmentDAO):
    def get_by_id(self, assignment_id: UUID) -> ReviewerAssignment | None:
        return self.session.get(ReviewerAssignment, assignment_id)

    def list_all(
        self,
        *,
        round_id: int | None = None,
        reviewer_id: UUID | None = None,
        reviewee_id: UUID | None = None,
    ) -> Sequence[ReviewerAssignment]:
        statement = select(ReviewerAssignment).where(
            col(ReviewerAssignment.round_id).in_(_active_round_ids())
        )
        if round_id is not None:
            statement = statement.where(ReviewerAssignment.round_id == round_id)
        if reviewer_id is not None:
            statement = statement.where(ReviewerAssignment.reviewer_id == reviewer_id)
        if reviewee_id is not None:
            statement = statement.where(ReviewerAssignment.reviewee_id == reviewee_id)
        statement = statement.order_by(col(ReviewerAssignment.created_at))
        return self.session.exec(statement).all()

    def list_by_reviewer(
        self, reviewer_id: UUID, *, round_id: int | None = None
    ) -> Sequence[ReviewerAssignment]:
        return self.list_all(round_id=round_id, reviewer_id=reviewer_id)

    def reviewee_ids(self, reviewer_id: UUID) -> Sequence[UUID]:
        statement = (
            select(ReviewerAssignment.reviewee_id)
            .where(
                ReviewerAssignment.reviewer_id == reviewer_id,
                col(ReviewerAssignment.round_id).in_(_active_round_ids()),
            )
            .distinct()
        )
        return self.session.exec(statement).all()

    def add(self, assignment: ReviewerAssignment) -> ReviewerAssignment:
        return self._add(assignment)

    def delete(self, assignment: ReviewerAssignment) -> None:
        self._delete(assignment)
