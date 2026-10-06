from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import exists, func
from sqlmodel import col, select

from app.v2.daos.rubric_dao import RubricDAO, RubricEntity
from app.v2.daos.sql.base import SqlDAO
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection, RubricVersion
from app.v2.models.submission import EvaluationRound, SubmissionEntry


class SqlRubricDAO(SqlDAO, RubricDAO):
    # --- version ---

    def get_version(self, version_id: int) -> RubricVersion | None:
        return self.session.get(RubricVersion, version_id)

    def get_version_by_code(self, code: str) -> RubricVersion | None:
        return self.session.exec(select(RubricVersion).where(RubricVersion.code == code)).first()

    def find_versions_page(self, *, limit: int, offset: int) -> tuple[Sequence[RubricVersion], int]:
        total = self.session.exec(select(func.count()).select_from(RubricVersion)).one()
        items = self.session.exec(
            select(RubricVersion).order_by(col(RubricVersion.id).desc()).offset(offset).limit(limit)
        ).all()
        return items, total

    def is_version_used_by_round(self, version_id: int) -> bool:
        statement = select(exists().where(EvaluationRound.rubric_version_id == version_id))
        return bool(self.session.exec(statement).one())

    # --- category ---

    def get_category(self, category_id: int) -> RubricCategory | None:
        return self.session.get(RubricCategory, category_id)

    def list_categories(self, version_id: int) -> Sequence[RubricCategory]:
        statement = (
            select(RubricCategory)
            .where(RubricCategory.version_id == version_id)
            .order_by(col(RubricCategory.sort_order), col(RubricCategory.id))
        )
        return self.session.exec(statement).all()

    # --- section ---

    def get_section(self, section_id: int) -> RubricSection | None:
        return self.session.get(RubricSection, section_id)

    def get_section_by_code(self, version_id: int, code: str) -> RubricSection | None:
        statement = (
            select(RubricSection)
            .join(RubricCategory, col(RubricCategory.id) == RubricSection.category_id)
            .where(RubricCategory.version_id == version_id, RubricSection.code == code)
        )
        return self.session.exec(statement).first()

    def list_sections(self, category_id: int) -> Sequence[RubricSection]:
        statement = (
            select(RubricSection)
            .where(RubricSection.category_id == category_id)
            .order_by(col(RubricSection.sort_order), col(RubricSection.id))
        )
        return self.session.exec(statement).all()

    def list_sections_of_version(self, version_id: int) -> Sequence[RubricSection]:
        statement = (
            select(RubricSection)
            .join(RubricCategory, col(RubricCategory.id) == RubricSection.category_id)
            .where(RubricCategory.version_id == version_id)
            .order_by(col(RubricSection.sort_order), col(RubricSection.id))
        )
        return self.session.exec(statement).all()

    def section_is_in_use(self, section_id: int) -> bool:
        has_children = exists().where(RubricSection.parent_id == section_id)
        has_items = exists().where(RubricItem.section_id == section_id)
        return bool(self.session.exec(select(has_children | has_items)).one())

    # --- item ---

    def get_item(self, item_id: int) -> RubricItem | None:
        return self.session.get(RubricItem, item_id)

    def list_items(self, section_id: int) -> Sequence[RubricItem]:
        statement = (
            select(RubricItem)
            .where(RubricItem.section_id == section_id)
            .order_by(col(RubricItem.id))
        )
        return self.session.exec(statement).all()

    def list_items_of_version(self, version_id: int) -> Sequence[RubricItem]:
        statement = (
            select(RubricItem)
            .join(RubricSection, col(RubricSection.id) == RubricItem.section_id)
            .join(RubricCategory, col(RubricCategory.id) == RubricSection.category_id)
            .where(RubricCategory.version_id == version_id)
            .order_by(col(RubricItem.id))
        )
        return self.session.exec(statement).all()

    def item_has_entries(self, item_id: int) -> bool:
        statement = select(exists().where(SubmissionEntry.item_id == item_id))
        return bool(self.session.exec(statement).one())

    # --- write ---

    def add[T: RubricEntity](self, entity: T) -> T:
        return self._add(entity)

    def update[T: RubricEntity](self, entity: T, values: Mapping[str, Any]) -> T:
        return self._update(entity, values)

    def delete(self, entity: RubricEntity) -> None:
        self._delete(entity)
