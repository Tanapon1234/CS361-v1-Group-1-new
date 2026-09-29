from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.research_interest import ResearchInterest


class ResearchInterestDAO(ABC):
    # --- master list (research_interest) ------------------------------------------

    @abstractmethod
    def get_by_id(self, research_interest_id: int) -> ResearchInterest | None: ...

    @abstractmethod
    def get_by_name(self, name: str) -> ResearchInterest | None: ...

    @abstractmethod
    def find_page(
        self, *, search: str | None, limit: int, offset: int, sort_order: str
    ) -> tuple[Sequence[ResearchInterest], int]: ...

    @abstractmethod
    def add(self, research_interest: ResearchInterest) -> ResearchInterest: ...

    @abstractmethod
    def update(
        self, research_interest: ResearchInterest, values: Mapping[str, Any]
    ) -> ResearchInterest: ...

    @abstractmethod
    def delete(self, research_interest: ResearchInterest) -> None: ...

    # --- per lecturer (faculty_research_interest) ------------------------------------

    @abstractmethod
    def list_by_lecturer(
        self, lecturer_id: UUID, *, search: str | None, sort_order: str
    ) -> Sequence[ResearchInterest]: ...

    @abstractmethod
    def replace_for_lecturer(self, lecturer_id: UUID, research_interest_ids: Sequence[int]) -> None:
        """Make these ids the lecturer's complete set of research interests."""

    @abstractmethod
    def remove_from_lecturer(self, lecturer_id: UUID, research_interest_id: int) -> bool:
        """Return False if it was not assigned."""
