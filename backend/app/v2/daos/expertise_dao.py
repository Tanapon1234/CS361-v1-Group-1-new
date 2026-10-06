from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.expertise import Expertise


class ExpertiseDAO(ABC):
    # --- master list (expertise) ---------------------------------------------------

    @abstractmethod
    def get_by_id(self, expertise_id: int) -> Expertise | None: ...

    @abstractmethod
    def find_page(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[Sequence[Expertise], int]: ...

    @abstractmethod
    def add(self, expertise: Expertise) -> Expertise: ...

    @abstractmethod
    def update(self, expertise: Expertise, values: Mapping[str, Any]) -> Expertise: ...

    @abstractmethod
    def delete(self, expertise: Expertise) -> None: ...

    # --- per lecturer (faculty_expertise) --------------------------------------------

    @abstractmethod
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Expertise]: ...

    @abstractmethod
    def replace_for_lecturer(self, lecturer_id: UUID, expertise_ids: Sequence[int]) -> None:
        """Make these ids the lecturer's complete set of expertise."""

    @abstractmethod
    def remove_from_lecturer(self, lecturer_id: UUID, expertise_id: int) -> bool:
        """Return False if it was not assigned."""
