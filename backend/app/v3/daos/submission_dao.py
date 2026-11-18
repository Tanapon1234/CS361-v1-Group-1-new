from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.enums import SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.submission import (
    Submission,
    SubmissionApproval,
    SubmissionCategoryTotal,
    SubmissionEntry,
)

type SubmissionEntity = Submission | SubmissionEntry | SubmissionApproval


class SubmissionDAO(ABC):
    """A submission with its entries, frozen category totals and approval history."""

    # --- submission ---

    @abstractmethod
    def get_by_id(self, submission_id: UUID) -> Submission | None: ...

    @abstractmethod
    def get_by_round_and_lecturer(self, round_id: int, lecturer_id: UUID) -> Submission | None: ...

    @abstractmethod
    def find_page(
        self,
        *,
        round_id: int | None,
        lecturer_id: UUID | None,
        department_id: int | None,
        status: SubmissionStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Submission], int]: ...

    @abstractmethod
    def list_with_lecturer(
        self, round_id: int, department_id: int | None
    ) -> Sequence[tuple[Submission, Lecturer]]:
        """Every submission of a round (for the report), with its lecturer."""

    @abstractmethod
    def list_department_category_totals(
        self,
        department_id: int,
        *,
        academic_year_from: int,
        academic_year_to: int,
        category_code: str | None = None,
        lecturer_id: UUID | None = None,
    ) -> Sequence[tuple[SubmissionCategoryTotal, Lecturer, int, str, str]]:
        """Frozen category totals of the department's submissions in the year range, as
        (total, lecturer, academic_year, category_code, category_name_th). Narrowed to
        one rubric category and/or one lecturer when given; always capped (see impl) so
        a growing department can't make this query unbounded."""

    @abstractmethod
    def find_lecturers_with_department_data(
        self, department_id: int, academic_year: int
    ) -> Sequence[UUID]:
        """Lecturer ids with at least one category total in this department and year."""

    # --- entries ---

    @abstractmethod
    def get_entry(self, entry_id: UUID) -> SubmissionEntry | None: ...

    @abstractmethod
    def list_entries(
        self, submission_id: UUID, *, section_id: int | None = None
    ) -> Sequence[SubmissionEntry]:
        """Ordered by sort_order, then creation time."""

    @abstractmethod
    def count_entries(
        self,
        submission_id: UUID,
        *,
        item_id: int | None = None,
        section_id: int | None = None,
        exclude_entry_id: UUID | None = None,
    ) -> int: ...

    # --- frozen totals ---

    @abstractmethod
    def list_category_totals(self, submission_id: UUID) -> Sequence[SubmissionCategoryTotal]: ...

    @abstractmethod
    def replace_category_totals(
        self, submission_id: UUID, totals: Sequence[SubmissionCategoryTotal]
    ) -> None: ...

    # --- approvals ---

    @abstractmethod
    def list_approvals(self, submission_id: UUID) -> Sequence[SubmissionApproval]:
        """Oldest first."""

    # --- write (submission, entry or approval) ---

    @abstractmethod
    def add[T: SubmissionEntity](self, entity: T) -> T: ...

    @abstractmethod
    def update[T: SubmissionEntity](self, entity: T, values: Mapping[str, Any]) -> T: ...

    @abstractmethod
    def delete(self, entity: Submission | SubmissionEntry) -> None:
        """Deleting a submission also deletes its entries (ON DELETE CASCADE)."""
