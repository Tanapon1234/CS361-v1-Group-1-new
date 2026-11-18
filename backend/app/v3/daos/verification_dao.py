"""Queues of things waiting for (or done by) a reviewer (migration 005)."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.v2.models.enums import VerificationStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import Publication
from app.v2.models.submission import EntryEvidence, Submission, SubmissionEntry


@dataclass(frozen=True, slots=True)
class EvidenceQueueRow:
    evidence: EntryEvidence
    entry: SubmissionEntry
    submission: Submission
    owner: Lecturer


class VerificationDAO(ABC):
    @abstractmethod
    def find_publications(
        self,
        status: VerificationStatus,
        *,
        limit: int,
        offset: int,
        reviewee_ids: Sequence[UUID] | None = None,
    ) -> tuple[Sequence[Publication], int]:
        """Oldest first, so the queue is worked in order. `reviewee_ids`, when given
        (V4 #293), narrows the queue to publications of at least one of those authors."""

    @abstractmethod
    def author_names(self, publication_id: int) -> list[str]:
        """name_th of the authors, in author order."""

    @abstractmethod
    def find_evidence(
        self,
        status: VerificationStatus,
        *,
        limit: int,
        offset: int,
        reviewee_ids: Sequence[UUID] | None = None,
    ) -> tuple[Sequence[EvidenceQueueRow], int]:
        """Uploaded files only (a pending upload has nothing to check), oldest first.
        `reviewee_ids`, when given (V4 #293), narrows the queue to that submission owner."""
