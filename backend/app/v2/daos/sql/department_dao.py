from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import func
from sqlmodel import select

from app.v2.daos.department_dao import DepartmentDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.department import Department


class SqlDepartmentDAO(SqlDAO, DepartmentDAO):
    def get_by_id(self, department_id: int) -> Department | None:
        return self.session.get(Department, department_id)

    def get_by_code(self, code: str) -> Department | None:
        return self.session.exec(select(Department).where(Department.code == code)).first()

    def find_page(
        self, *, is_active: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[Department], int]:
        statement = select(Department)
        if is_active is not None:
            statement = statement.where(Department.is_active == is_active)
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(Department.code).offset(offset).limit(limit)
        ).all()
        return items, total

    def add(self, department: Department) -> Department:
        return self._add(department)

    def update(self, department: Department, values: Mapping[str, Any]) -> Department:
        return self._update(department, values)
