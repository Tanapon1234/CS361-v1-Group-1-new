from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.research_interest import ResearchInterest


class SqlResearchInterestDAO(SqlDAO, ResearchInterestDAO):
    def get_by_id(self, research_interest_id: int) -> ResearchInterest | None:
        raise NotImplementedError

    def find_page(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[Sequence[ResearchInterest], int]:
        raise NotImplementedError

    def add(self, research_interest: ResearchInterest) -> ResearchInterest:
        raise NotImplementedError

    def update(
        self, research_interest: ResearchInterest, values: Mapping[str, Any]
    ) -> ResearchInterest:
        raise NotImplementedError

    def delete(self, research_interest: ResearchInterest) -> None:
        raise NotImplementedError

    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[ResearchInterest]:
        raise NotImplementedError

    def replace_for_lecturer(self, lecturer_id: UUID, research_interest_ids: Sequence[int]) -> None:
        raise NotImplementedError

    def remove_from_lecturer(self, lecturer_id: UUID, research_interest_id: int) -> bool:
        raise NotImplementedError
