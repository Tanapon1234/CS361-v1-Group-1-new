from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_
from sqlmodel import select

from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.lecturer import Lecturer


class SqlLecturerDAO(SqlDAO, LecturerDAO):
    def get_by_id(self, lecturer_id: UUID) -> Lecturer | None:
        return self.session.get(Lecturer, lecturer_id)

    def get_by_email(self, email: str) -> Lecturer | None:
        statement = select(Lecturer).where(Lecturer.email == email)
        return self.session.exec(statement).first()

    def get_by_cognito_sub(self, cognito_sub: str) -> Lecturer | None:
        statement = select(Lecturer).where(Lecturer.cognito_sub == cognito_sub)
        return self.session.exec(statement).first()

    def find_page(
        self,
        *,
        q: str | None,
        is_active: bool | None,
        limit: int,
        offset: int,
        department_id: int | None = None,
    ) -> tuple[Sequence[Lecturer], int]:
        statement = select(Lecturer)
        count_statement = select(func.count()).select_from(Lecturer)

        if q:
            pattern = f"%{q}%"
            search_filter = or_(
                Lecturer.name_th.ilike(pattern),
                Lecturer.name_en.ilike(pattern),
                Lecturer.email.ilike(pattern),
            )
            statement = statement.where(search_filter)
            count_statement = count_statement.where(search_filter)

        if is_active is not None:
            statement = statement.where(Lecturer.is_active == is_active)
            count_statement = count_statement.where(Lecturer.is_active == is_active)

        if department_id is not None:
            statement = statement.where(Lecturer.department_id == department_id)
            count_statement = count_statement.where(Lecturer.department_id == department_id)

        total = self.session.exec(count_statement).one()
        items = self.session.exec(
            statement.order_by(Lecturer.name_th.asc(), Lecturer.lecturer_id.asc())
            .offset(offset)
            .limit(limit)
        ).all()
        return items, total

    def add(self, lecturer: Lecturer) -> Lecturer:
        self.session.add(lecturer)
        self.session.flush()
        self.session.refresh(lecturer)
        return lecturer

    def update(self, lecturer: Lecturer, values: Mapping[str, Any]) -> Lecturer:
        lecturer.sqlmodel_update(values)
        self.session.flush()
        self.session.refresh(lecturer)
        return lecturer
