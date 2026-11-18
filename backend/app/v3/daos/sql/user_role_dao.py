from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select

from app.v2.models.user_role import UserRole
from app.v3.daos.sql.base import SqlDAO
from app.v3.daos.user_role_dao import UserRoleDAO


class SqlUserRoleDAO(SqlDAO, UserRoleDAO):
    def get(self, lecturer_id: UUID, role: str) -> UserRole | None:
        return self.session.get(UserRole, (lecturer_id, role))

    def list_all(self, *, lecturer_id: UUID | None = None) -> Sequence[UserRole]:
        statement = select(UserRole)
        if lecturer_id is not None:
            statement = statement.where(UserRole.lecturer_id == lecturer_id)
        statement = statement.order_by(col(UserRole.created_at))
        return self.session.exec(statement).all()

    def roles_of(self, lecturer_id: UUID) -> Sequence[str]:
        statement = select(UserRole.role).where(UserRole.lecturer_id == lecturer_id)
        return self.session.exec(statement).all()

    def count_with_role(self, role: str) -> int:
        statement = select(func.count()).select_from(UserRole).where(UserRole.role == role)
        return self.session.exec(statement).one()

    def add(self, user_role: UserRole) -> UserRole:
        return self._add(user_role)

    def delete(self, user_role: UserRole) -> None:
        self._delete(user_role)
