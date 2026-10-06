from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.expertise import Expertise


class SqlExpertiseDAO(SqlDAO, ExpertiseDAO):
    def get_by_id(self, expertise_id: int) -> Expertise | None:
        raise NotImplementedError

    def find_page(
        self, *, q: str | None, limit: int, offset: int
    ) -> tuple[Sequence[Expertise], int]:
        raise NotImplementedError

    def add(self, expertise: Expertise) -> Expertise:
        raise NotImplementedError

    def update(self, expertise: Expertise, values: Mapping[str, Any]) -> Expertise:
        raise NotImplementedError

    def delete(self, expertise: Expertise) -> None:
        raise NotImplementedError

    def list_by_lecturer(self, lecturer_id: UUID) -> Sequence[Expertise]:
        raise NotImplementedError

    def replace_for_lecturer(self, lecturer_id: UUID, expertise_ids: Sequence[int]) -> None:
        raise NotImplementedError

    def remove_from_lecturer(self, lecturer_id: UUID, expertise_id: int) -> bool:
        raise NotImplementedError
