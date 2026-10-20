from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

from app.v2.models.publication import Publication


class PublicationDAO(ABC):
    @abstractmethod
    def get_by_id(self, publication_id: int) -> Publication | None: ...

    @abstractmethod
    def get_by_doi(self, doi: str) -> Publication | None: ...

    @abstractmethod
    def find_page(
        self,
        *,
        q: str | None,
        publication_year: int | None,
        lecturer_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Publication], int]:
        """`lecturer_id` limits results to that lecturer's publications."""

    @abstractmethod
    def find_lecturer_page(
        self,
        lecturer_id: UUID,
        *,
        q: str | None,
        publication_year: int | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[tuple[Publication, int | None]], int]: ...

    @abstractmethod
    def add(self, publication: Publication) -> Publication: ...

    @abstractmethod
    def update(self, publication: Publication, values: Mapping[str, Any]) -> Publication: ...

    @abstractmethod
    def delete(self, publication: Publication) -> None: ...

    # --- authors (faculty_publication) ------------------------------------------------

    @abstractmethod
    def get_author_ids(self, publication_id: int) -> list[UUID]:
        """Lecturer ids ordered by author_order."""

    @abstractmethod
    def set_authors(self, publication_id: int, lecturer_ids: Sequence[UUID]) -> None:
        """Replace all authors; list position becomes author_order."""
