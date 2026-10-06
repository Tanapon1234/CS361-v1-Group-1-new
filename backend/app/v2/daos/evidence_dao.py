from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.submission import EntryEvidence


class EvidenceDAO(ABC):
    @abstractmethod
    def get_by_id(self, evidence_id: UUID) -> EntryEvidence | None: ...

    @abstractmethod
    def list_by_entry(self, entry_id: UUID) -> Sequence[EntryEvidence]:
        """Oldest first."""

    @abstractmethod
    def list_by_submission(self, submission_id: UUID) -> Sequence[EntryEvidence]: ...

    @abstractmethod
    def add(self, evidence: EntryEvidence) -> EntryEvidence: ...

    @abstractmethod
    def update(self, evidence: EntryEvidence, values: Mapping[str, Any]) -> EntryEvidence: ...

    @abstractmethod
    def delete(self, evidence: EntryEvidence) -> None: ...
