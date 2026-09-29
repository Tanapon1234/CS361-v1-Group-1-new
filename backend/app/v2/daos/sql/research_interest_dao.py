from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import select

from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.research_interest import ResearchInterest


class SqlResearchInterestDAO(SqlDAO, ResearchInterestDAO):
    def get_by_id(self, research_interest_id: int) -> ResearchInterest | None:
        return self.session.get(ResearchInterest, research_interest_id)

    def get_by_name(self, name: str) -> ResearchInterest | None:
        statement = select(ResearchInterest).where(ResearchInterest.name == name)
        return self.session.exec(statement).first()

    def find_page(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[Sequence[ResearchInterest], int]:
        statement = select(ResearchInterest)
        count_statement = select(func.count()).select_from(ResearchInterest)

        if q:
            pattern = f"%{q}%"
            statement = statement.where(ResearchInterest.name.ilike(pattern))
            count_statement = count_statement.where(ResearchInterest.name.ilike(pattern))

        total = self.session.exec(count_statement).one()
        items = self.session.exec(
            statement.order_by(ResearchInterest.name).offset(offset).limit(limit)
        ).all()
        return items, total

    def add(self, research_interest: ResearchInterest) -> ResearchInterest:
        self.session.add(research_interest)
        self.session.flush()
        self.session.refresh(research_interest)
        return research_interest

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
