"""Read-only view of what one lecturer did: workload entries and publications, by year."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.v2.models.publication import Publication
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection
from app.v2.models.submission import EvaluationRound, Submission, SubmissionEntry


@dataclass(frozen=True, slots=True)
class WorkEntryRow:
    entry: SubmissionEntry
    item: RubricItem
    section: RubricSection
    category: RubricCategory
    submission: Submission
    round: EvaluationRound


class LecturerWorkDAO(ABC):
    @abstractmethod
    def list_entries(
        self, lecturer_id: UUID, *, academic_year: int | None, category_code: str | None
    ) -> Sequence[WorkEntryRow]:
        """Entries of every submission of the lecturer, newest round first."""

    @abstractmethod
    def list_publications(
        self, lecturer_id: UUID, *, publication_year: int | None
    ) -> Sequence[tuple[Publication, int | None]]:
        """Publications the lecturer authored, with their author_order."""

    @abstractmethod
    def list_entry_years(self, lecturer_id: UUID) -> list[int]:
        """Academic years of the rounds the lecturer has entries in."""

    @abstractmethod
    def list_publication_years(self, lecturer_id: UUID) -> list[int]:
        """publication_year values (C.E.) of the lecturer's publications."""

    @abstractmethod
    def get_category_name(self, code: str) -> str | None:
        """name_th of a rubric category code, from the newest rubric version that has it."""
