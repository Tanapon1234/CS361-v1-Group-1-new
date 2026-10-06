from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.lecturer import Lecturer
from app.v2.models.member_position import MemberPosition
from app.v2.models.rubric import RubricItem
from app.v2.models.submission import EntryAssessment, Submission, SubmissionEntry

type QueueRow = tuple[SubmissionEntry, Submission, RubricItem, Lecturer, EntryAssessment | None]


class AssessmentDAO(ABC):
    @abstractmethod
    def list_by_entry(self, entry_id: UUID) -> Sequence[EntryAssessment]:
        """Oldest first."""

    @abstractmethod
    def list_by_entries(self, entry_ids: Sequence[UUID]) -> Sequence[EntryAssessment]: ...

    @abstractmethod
    def get_by_entry_and_assessor(
        self, entry_id: UUID, assessor_id: UUID
    ) -> EntryAssessment | None: ...

    @abstractmethod
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
        """Entries of `assessing` submissions whose item one of `positions` may assess.

        A department-level position only covers submissions of its own department.
        `assessed`: True = the assessor already gave a value, False = not yet, None = both.
        """

    @abstractmethod
    def add(self, assessment: EntryAssessment) -> EntryAssessment: ...

    @abstractmethod
    def update(self, assessment: EntryAssessment, values: Mapping[str, Any]) -> EntryAssessment: ...

    @abstractmethod
    def delete(self, assessment: EntryAssessment) -> None: ...
