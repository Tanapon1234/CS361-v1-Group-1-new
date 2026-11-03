from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.publication import PublicationEvidence


class PublicationEvidenceDAO(ABC):
    @abstractmethod
    def get_by_id(self, evidence_id: UUID) -> PublicationEvidence | None: ...

    @abstractmethod
    def list_by_publication(self, publication_id: int) -> Sequence[PublicationEvidence]:
        """Oldest first."""

    @abstractmethod
    def add(self, evidence: PublicationEvidence) -> PublicationEvidence: ...

    @abstractmethod
    def update(
        self, evidence: PublicationEvidence, values: Mapping[str, Any]
    ) -> PublicationEvidence: ...

    @abstractmethod
    def delete(self, evidence: PublicationEvidence) -> None: ...
