from collections.abc import Sequence
from uuid import UUID

from sqlmodel import col, select

from app.v2.models.reviewer_assignment import ReviewerAssignment
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.daos.sql.base import SqlDAO


class SqlReviewerAssignmentDAO(SqlDAO, ReviewerAssignmentDAO):
    def get_by_id(self, assignment_id: UUID) -> ReviewerAssignment | None:
        return self.session.get(ReviewerAssignment, assignment_id)

    def list_all(
        self, *, reviewer_id: UUID | None = None, reviewee_id: UUID | None = None
    ) -> Sequence[ReviewerAssignment]:
        statement = select(ReviewerAssignment)
        if reviewer_id is not None:
            statement = statement.where(ReviewerAssignment.reviewer_id == reviewer_id)
        if reviewee_id is not None:
            statement = statement.where(ReviewerAssignment.reviewee_id == reviewee_id)
        statement = statement.order_by(col(ReviewerAssignment.created_at))
        return self.session.exec(statement).all()

    def list_by_reviewer(self, reviewer_id: UUID) -> Sequence[ReviewerAssignment]:
        return self.list_all(reviewer_id=reviewer_id)

    def reviewee_ids(self, reviewer_id: UUID) -> Sequence[UUID]:
        statement = select(ReviewerAssignment.reviewee_id).where(
            ReviewerAssignment.reviewer_id == reviewer_id
        )
        return self.session.exec(statement).all()

    def add(self, assignment: ReviewerAssignment) -> ReviewerAssignment:
        return self._add(assignment)

    def delete(self, assignment: ReviewerAssignment) -> None:
        self._delete(assignment)
