from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func
from sqlmodel import col, select

from app.v2.models.expertise import Expertise, FacultyExpertise
from app.v3.daos.expertise_dao import ExpertiseDAO
from app.v3.daos.sql.base import SqlDAO


class SqlExpertiseDAO(SqlDAO, ExpertiseDAO):
    def get_by_id(self, expertise_id: int) -> Expertise | None:
        return self.session.get(Expertise, expertise_id)

    def get_by_description(self, description: str) -> Expertise | None:
        statement = select(Expertise).where(
            func.lower(Expertise.description) == description.lower()
        )
        return self.session.exec(statement).first()

    def find_page(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[Sequence[Expertise], int]:
        statement = select(Expertise)
        if q:
            statement = statement.where(col(Expertise.description).ilike(f"%{q}%"))

        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(col(Expertise.description).asc()).offset(offset).limit(limit)
        ).all()
        return items, total

    def add(self, expertise: Expertise) -> Expertise:
        return self._add(expertise)

    def update(self, expertise: Expertise, values: Mapping[str, Any]) -> Expertise:
        return self._update(expertise, values)

    def delete(self, expertise: Expertise) -> None:
        self._delete(expertise)

    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Expertise]:
        statement = (
            select(Expertise)
            .join(FacultyExpertise, FacultyExpertise.expertise_id == Expertise.expertise_id)
            .where(FacultyExpertise.lecturer_id == lecturer_id)
            .order_by(col(Expertise.description).asc())
        )
        return self.session.exec(statement).all()

    def replace_for_lecturer(self, lecturer_id: UUID, expertise_ids: Sequence[int]) -> None:
        self.session.exec(
            delete(FacultyExpertise).where(FacultyExpertise.lecturer_id == lecturer_id)
        )
        self.session.add_all(
            FacultyExpertise(lecturer_id=lecturer_id, expertise_id=expertise_id)
            for expertise_id in expertise_ids
        )
        self.session.flush()

    def remove_from_lecturer(self, lecturer_id: UUID, expertise_id: int) -> bool:
        link = self.session.get(FacultyExpertise, (lecturer_id, expertise_id))
        if link is None:
            return False
        self._delete(link)
        return True
