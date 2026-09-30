from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import select

from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.research_interest import FacultyResearchInterest, ResearchInterest


class SqlResearchInterestDAO(SqlDAO, ResearchInterestDAO):
    def get_by_id(self, research_interest_id: int) -> ResearchInterest | None:
        return self.session.get(ResearchInterest, research_interest_id)

    def get_by_name(self, name: str) -> ResearchInterest | None:
        statement = select(ResearchInterest).where(ResearchInterest.name == name)
        return self.session.exec(statement).first()

    def find_page(
        self, *, search: str | None, limit: int, offset: int, sort_order: str
    ) -> tuple[Sequence[ResearchInterest], int]:
        statement = select(ResearchInterest)
        count_statement = select(func.count()).select_from(ResearchInterest)

        if search:
            pattern = f"%{search}%"
            statement = statement.where(ResearchInterest.name.ilike(pattern))
            count_statement = count_statement.where(ResearchInterest.name.ilike(pattern))

        order_by = (
            ResearchInterest.name.desc()
            if sort_order == "desc"
            else ResearchInterest.name.asc()
        )
        total = self.session.exec(count_statement).one()
        items = self.session.exec(statement.order_by(order_by).offset(offset).limit(limit)).all()
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

    def list_by_lecturer(
        self, lecturer_id: UUID, *, search: str | None, sort_order: str
    ) -> Sequence[ResearchInterest]:
        statement = (
            select(ResearchInterest)
            .join(
                FacultyResearchInterest,
                FacultyResearchInterest.research_interest_id
                == ResearchInterest.research_interest_id,
            )
            .where(FacultyResearchInterest.lecturer_id == lecturer_id)
        )

        if search:
            statement = statement.where(ResearchInterest.name.ilike(f"%{search}%"))

        order_by = (
            ResearchInterest.name.desc()
            if sort_order == "desc"
            else ResearchInterest.name.asc()
        )
        return self.session.exec(statement.order_by(order_by)).all()

    def replace_for_lecturer(self, lecturer_id: UUID, research_interest_ids: Sequence[int]) -> None:
        raise NotImplementedError

    def remove_from_lecturer(self, lecturer_id: UUID, research_interest_id: int) -> bool:
        raise NotImplementedError
