from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from sqlmodel import col, select

from app.v2.models.education import Education
from app.v3.daos.education_dao import EducationDAO
from app.v3.daos.sql.base import SqlDAO


class SqlEducationDAO(SqlDAO, EducationDAO):
    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Education]:
        statement = (
            select(Education)
            .where(Education.lecturer_id == lecturer_id)
            # Latest degree first; rows without a year go last
            .order_by(
                col(Education.graduation_year).desc().nulls_last(),
                col(Education.education_id).asc(),
            )
        )
        return self.session.exec(statement).all()

    def get_by_id(self, education_id: int) -> Education | None:
        return self.session.get(Education, education_id)

    def add(self, education: Education) -> Education:
        return self._add(education)

    def update(self, education: Education, values: Mapping[str, Any]) -> Education:
        return self._update(education, values)

    def delete(self, education: Education) -> None:
        self._delete(education)
