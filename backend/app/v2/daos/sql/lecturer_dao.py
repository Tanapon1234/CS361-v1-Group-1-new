from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

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

    def find_page(
        self, *, q: str | None, is_active: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[Lecturer], int]:
        raise NotImplementedError

    def add(self, lecturer: Lecturer) -> Lecturer:
        self.session.add(lecturer)
        self.session.flush()
        self.session.refresh(lecturer)
        return lecturer

    def update(self, lecturer: Lecturer, values: Mapping[str, Any]) -> Lecturer:
        raise NotImplementedError
