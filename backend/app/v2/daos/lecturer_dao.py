from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.lecturer import Lecturer


class LecturerDAO(ABC):
    @abstractmethod
    def get_by_id(self, lecturer_id: UUID) -> Lecturer | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Lecturer | None: ...

    @abstractmethod
    def find_page(
        self, *, q: str | None, is_active: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[Lecturer], int]:
        """Return one page of lecturers and the total number of matches."""

    @abstractmethod
    def add(self, lecturer: Lecturer) -> Lecturer: ...

    @abstractmethod
    def update(self, lecturer: Lecturer, values: Mapping[str, Any]) -> Lecturer: ...
