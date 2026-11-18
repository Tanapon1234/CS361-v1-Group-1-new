"""Who reviews whom, per evaluation round (011/012_reviewer_assignment*.sql, V4 #293).

An assignment is "active" only while its round is open and before the round's
submit_due_at; list_all / list_by_reviewer / reviewee_ids return active ones only.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.v2.models.reviewer_assignment import ReviewerAssignment


class ReviewerAssignmentDAO(ABC):
    @abstractmethod
    def get_by_id(self, assignment_id: UUID) -> ReviewerAssignment | None: ...

    @abstractmethod
    def list_all(
        self,
        *,
        round_id: int | None = None,
        reviewer_id: UUID | None = None,
        reviewee_id: UUID | None = None,
    ) -> Sequence[ReviewerAssignment]:
        """Every active assignment, optionally narrowed by round, reviewer and/or reviewee."""

    @abstractmethod
    def list_by_reviewer(
        self, reviewer_id: UUID, *, round_id: int | None = None
    ) -> Sequence[ReviewerAssignment]: ...

    @abstractmethod
    def reviewee_ids(self, reviewer_id: UUID) -> Sequence[UUID]:
        """Just the lecturer_ids this reviewer may see in the verification queue (active rounds)."""

    @abstractmethod
    def is_assigned(self, reviewer_id: UUID, reviewee_id: UUID, round_id: int) -> bool:
        """True while this reviewer is assigned to this lecturer in this round and the round
        is still accepting work."""

    @abstractmethod
    def has_reviewer(self, reviewee_id: UUID, round_id: int) -> bool:
        """True while someone is assigned to review this lecturer in this round and the round
        is still accepting work (so the department head signs the first step when it is False)."""

    @abstractmethod
    def add(self, assignment: ReviewerAssignment) -> ReviewerAssignment: ...

    @abstractmethod
    def delete(self, assignment: ReviewerAssignment) -> None: ...
