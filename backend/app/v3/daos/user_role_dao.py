"""Roles an admin grants from the app (013_user_role.sql)."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.v2.models.user_role import UserRole


class UserRoleDAO(ABC):
    @abstractmethod
    def get(self, lecturer_id: UUID, role: str) -> UserRole | None: ...

    @abstractmethod
    def list_all(self, *, lecturer_id: UUID | None = None) -> Sequence[UserRole]: ...

    @abstractmethod
    def roles_of(self, lecturer_id: UUID) -> Sequence[str]:
        """Just the role names this lecturer was granted."""

    @abstractmethod
    def count_with_role(self, role: str) -> int: ...

    @abstractmethod
    def add(self, user_role: UserRole) -> UserRole: ...

    @abstractmethod
    def delete(self, user_role: UserRole) -> None: ...
