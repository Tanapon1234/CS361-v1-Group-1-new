from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlmodel import col, select

from app.v2.models.submission_review import SubmissionReview
from app.v3.daos.sql.base import SqlDAO
from app.v3.daos.submission_review_dao import SubmissionReviewDAO


class SqlSubmissionReviewDAO(SqlDAO, SubmissionReviewDAO):
    def get(self, submission_id: UUID) -> SubmissionReview | None:
        return self.session.get(SubmissionReview, submission_id)

    def get_many(self, submission_ids: Sequence[UUID]) -> Sequence[SubmissionReview]:
        if not submission_ids:
            return []
        statement = select(SubmissionReview).where(
            col(SubmissionReview.submission_id).in_(submission_ids)
        )
        return self.session.exec(statement).all()

    def add(self, review: SubmissionReview) -> SubmissionReview:
        return self._add(review)

    def update(self, review: SubmissionReview, values: Mapping[str, Any]) -> SubmissionReview:
        return self._update(review, values)
