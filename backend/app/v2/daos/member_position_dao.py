from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any
from uuid import UUID

from app.v2.models.enums import PositionCode
from app.v2.models.member_position import MemberPosition


class MemberPositionDAO(ABC):
    @abstractmethod
    def get_by_id(self, position_id: UUID) -> MemberPosition | None: ...

    @abstractmethod
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[MemberPosition]:
        """Newest term first."""

    @abstractmethod
    def list_active(self, lecturer_id: UUID, on: date) -> Sequence[MemberPosition]:
        """Positions held on `on` (start_date <= on and end_date is NULL or after it)."""

    @abstractmethod
    def find_overlapping(
        self,
        *,
        lecturer_id: UUID,
        position: PositionCode,
        start_date: date,
        end_date: date | None,
        exclude_id: UUID | None = None,
    ) -> MemberPosition | None:
        """Another term of the same lecturer and position whose dates overlap."""

    @abstractmethod
    def add(self, position: MemberPosition) -> MemberPosition: ...

    @abstractmethod
    def update(self, position: MemberPosition, values: Mapping[str, Any]) -> MemberPosition: ...

    @abstractmethod
    def delete(self, position: MemberPosition) -> None: ...
