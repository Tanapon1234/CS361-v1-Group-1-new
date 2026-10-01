from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.lecturer import Lecturer


class SqlLecturerDAO(SqlDAO, LecturerDAO):
    def get_by_id(self, lecturer_id: UUID) -> Lecturer | None:
        return self.session.get(Lecturer, lecturer_id)

    def find_page(
        self, *, q: str | None, is_active: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[Lecturer], int]:
        raise NotImplementedError

    def add(self, lecturer: Lecturer) -> Lecturer:
        raise NotImplementedError

    def update(self, lecturer: Lecturer, values: Mapping[str, Any]) -> Lecturer:
        raise NotImplementedError
