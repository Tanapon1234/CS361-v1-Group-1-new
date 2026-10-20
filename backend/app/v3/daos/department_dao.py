from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.v2.models.department import Department


class DepartmentDAO(ABC):
    @abstractmethod
    def get_by_id(self, department_id: int) -> Department | None: ...

    @abstractmethod
    def get_by_code(self, code: str) -> Department | None: ...

    @abstractmethod
    def find_page(
        self, *, is_active: bool | None, limit: int, offset: int
    ) -> tuple[Sequence[Department], int]: ...

    @abstractmethod
    def add(self, department: Department) -> Department: ...

    @abstractmethod
    def update(self, department: Department, values: Mapping[str, Any]) -> Department: ...
