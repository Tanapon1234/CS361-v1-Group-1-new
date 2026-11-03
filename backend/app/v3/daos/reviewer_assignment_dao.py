"""Who reviews whom (011_reviewer_assignment.sql, V4 #293)."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.v2.models.reviewer_assignment import ReviewerAssignment


class ReviewerAssignmentDAO(ABC):
    @abstractmethod
    def get_by_id(self, assignment_id: UUID) -> ReviewerAssignment | None: ...

    @abstractmethod
    def list_all(
        self, *, reviewer_id: UUID | None = None, reviewee_id: UUID | None = None
    ) -> Sequence[ReviewerAssignment]:
        """Every assignment, optionally narrowed by reviewer and/or reviewee."""

    @abstractmethod
    def list_by_reviewer(self, reviewer_id: UUID) -> Sequence[ReviewerAssignment]: ...

    @abstractmethod
    def reviewee_ids(self, reviewer_id: UUID) -> Sequence[UUID]:
        """Just the lecturer_ids this reviewer may see in the verification queue."""

    @abstractmethod
    def add(self, assignment: ReviewerAssignment) -> ReviewerAssignment: ...

    @abstractmethod
    def delete(self, assignment: ReviewerAssignment) -> None: ...
