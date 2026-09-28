from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.daos.publication_dao import PublicationDAO
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.publication import Publication


class SqlPublicationDAO(SqlDAO, PublicationDAO):
    def get_by_id(self, publication_id: int) -> Publication | None:
        raise NotImplementedError

    def find_page(
        self,
        *,
        q: str | None,
        publication_year: int | None,
        lecturer_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Publication], int]:
        raise NotImplementedError

    def add(self, publication: Publication) -> Publication:
        raise NotImplementedError

    def update(self, publication: Publication, values: Mapping[str, Any]) -> Publication:
        raise NotImplementedError

    def delete(self, publication: Publication) -> None:
        raise NotImplementedError

    def get_author_ids(self, publication_id: int) -> list[UUID]:
        raise NotImplementedError

    def set_authors(self, publication_id: int, lecturer_ids: Sequence[UUID]) -> None:
        raise NotImplementedError
