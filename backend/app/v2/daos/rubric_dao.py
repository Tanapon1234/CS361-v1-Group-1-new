from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection, RubricVersion

type RubricEntity = RubricVersion | RubricCategory | RubricSection | RubricItem


class RubricDAO(ABC):
    """The versioned rubric: version -> category -> section -> item."""

    # --- version ---

    @abstractmethod
    def get_version(self, version_id: int) -> RubricVersion | None: ...

    @abstractmethod
    def get_version_by_code(self, code: str) -> RubricVersion | None: ...

    @abstractmethod
    def find_versions_page(
        self, *, limit: int, offset: int
    ) -> tuple[Sequence[RubricVersion], int]: ...

    @abstractmethod
    def is_version_used_by_round(self, version_id: int) -> bool: ...

    # --- category ---

    @abstractmethod
    def get_category(self, category_id: int) -> RubricCategory | None: ...

    @abstractmethod
    def list_categories(self, version_id: int) -> Sequence[RubricCategory]:
        """Ordered by sort_order."""

    # --- section ---

    @abstractmethod
    def get_section(self, section_id: int) -> RubricSection | None: ...

    @abstractmethod
    def get_section_by_code(self, version_id: int, code: str) -> RubricSection | None: ...

    @abstractmethod
    def list_sections(self, category_id: int) -> Sequence[RubricSection]: ...

    @abstractmethod
    def list_sections_of_version(self, version_id: int) -> Sequence[RubricSection]: ...

    @abstractmethod
    def section_is_in_use(self, section_id: int) -> bool:
        """True if the section still has sub-sections or items."""

    # --- item ---

    @abstractmethod
    def get_item(self, item_id: int) -> RubricItem | None: ...

    @abstractmethod
    def list_items(self, section_id: int) -> Sequence[RubricItem]: ...

    @abstractmethod
    def list_items_of_version(self, version_id: int) -> Sequence[RubricItem]: ...

    @abstractmethod
    def item_has_entries(self, item_id: int) -> bool: ...

    # --- write (any rubric entity) ---

    @abstractmethod
    def add[T: RubricEntity](self, entity: T) -> T: ...

    @abstractmethod
    def update[T: RubricEntity](self, entity: T, values: Mapping[str, Any]) -> T: ...

    @abstractmethod
    def delete(self, entity: RubricEntity) -> None: ...
