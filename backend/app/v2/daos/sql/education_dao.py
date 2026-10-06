from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.education import Education


class SqlEducationDAO(SqlDAO, EducationDAO):
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Education]:
        raise NotImplementedError

    def get_by_id(self, education_id: int) -> Education | None:
        raise NotImplementedError

    def add(self, education: Education) -> Education:
        raise NotImplementedError

    def update(self, education: Education, values: Mapping[str, Any]) -> Education:
        raise NotImplementedError

    def delete(self, education: Education) -> None:
        raise NotImplementedError
