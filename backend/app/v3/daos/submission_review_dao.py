"""A reviewer's verdict on a whole sheet (014_submission_review.sql)."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.submission_review import SubmissionReview


class SubmissionReviewDAO(ABC):
    @abstractmethod
    def get(self, submission_id: UUID) -> SubmissionReview | None: ...

    @abstractmethod
    def get_many(self, submission_ids: Sequence[UUID]) -> Sequence[SubmissionReview]: ...

    @abstractmethod
    def add(self, review: SubmissionReview) -> SubmissionReview: ...

    @abstractmethod
    def update(self, review: SubmissionReview, values: Mapping[str, Any]) -> SubmissionReview: ...
