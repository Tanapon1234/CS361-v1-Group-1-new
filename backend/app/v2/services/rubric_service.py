"""Versioned workload rubric: version -> category -> section -> item.

A version that an evaluation round uses is locked ("ล็อกเกณฑ์ของรอบ"): its structure can no
longer change, so scores already given stay valid. The only change still allowed is turning
an item on or off (`is_active`). To change a locked rubric, create a new version from it
(`source_version_id`).
"""

from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageQuery, PageResponse
from app.v2.dtos.rubric_dto import (
    FieldSpec,
    RubricCategoryCreateRequest,
    RubricCategoryResponse,
    RubricFormCategory,
    RubricFormResponse,
    RubricFormSection,
    RubricItemCreateRequest,
    RubricItemFields,
    RubricItemResponse,
    RubricItemUpdateRequest,
    RubricSectionCreateRequest,
    RubricSectionResponse,
    RubricSectionUpdateRequest,
    RubricVersionCreateRequest,
    RubricVersionResponse,
    RubricVersionUpdateRequest,
)
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection, RubricVersion
from app.v2.services.db_errors import is_unique_violation

LOCKED = "Rubric version is used by an evaluation round and can no longer change"


def _field_schema_json(field_schema: Mapping[str, FieldSpec] | None) -> dict[str, Any] | None:
    if field_schema is None:
        return None
    return {name: spec.model_dump(exclude_none=True) for name, spec in field_schema.items()}


def _validation_message(exc: ValidationError) -> str:
    return "; ".join(error["msg"].removeprefix("Value error, ") for error in exc.errors())


class RubricService:
    def __init__(self, rubric_dao: RubricDAO) -> None:
        self.rubric_dao = rubric_dao

    # --- versions -----------------------------------------------------------------

    def list_versions(self, query: PageQuery) -> PageResponse[RubricVersionResponse]:
        items, total = self.rubric_dao.find_versions_page(limit=query.limit, offset=query.offset)
        return PageResponse(
            items=[RubricVersionResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )

    def create_version(self, data: RubricVersionCreateRequest) -> RubricVersionResponse:
        source = None
        if data.source_version_id is not None:
            source = self.rubric_dao.get_version(data.source_version_id)
            if source is None:
                raise BadRequestError("Source rubric version not found")
        if self.rubric_dao.get_version_by_code(data.code) is not None:
            raise ConflictError("Rubric version code already used")

        version = self._add(RubricVersion(**data.model_dump(exclude={"source_version_id"})))
        if source is not None:
            self._copy_structure(source.id, version.id)
        return RubricVersionResponse.model_validate(version)

    def get_version(self, version_id: int) -> RubricVersionResponse:
        return RubricVersionResponse.model_validate(self._require_version(version_id))

    def update_version(
        self, version_id: int, data: RubricVersionUpdateRequest
    ) -> RubricVersionResponse:
        version = self._require_version(version_id)
        self._require_unlocked(version_id)
        values = data.model_dump(exclude_unset=True)
        code = values.get("code")
        if (
            code is not None
            and code != version.code
            and self.rubric_dao.get_version_by_code(code) is not None
        ):
            raise ConflictError("Rubric version code already used")
        return RubricVersionResponse.model_validate(self._update(version, values))

    def get_form(self, version_id: int) -> RubricFormResponse:
        """The whole rubric in one tree: category -> section (-> sub-section) -> item."""
        version = self._require_version(version_id)
        categories = self.rubric_dao.list_categories(version_id)
        sections = self.rubric_dao.list_sections_of_version(version_id)
        items = self.rubric_dao.list_items_of_version(version_id)

        items_by_section: dict[int, list[RubricItemResponse]] = defaultdict(list)
        for item in items:
            items_by_section[item.section_id].append(RubricItemResponse.model_validate(item))
        section_ids = {section.id for section in sections}
        children: dict[int | None, list[RubricSection]] = defaultdict(list)
        for section in sections:
            parent = section.parent_id if section.parent_id in section_ids else None
            children[parent].append(section)

        def build(section: RubricSection) -> RubricFormSection:
            return RubricFormSection(
                **RubricSectionResponse.model_validate(section).model_dump(),
                items=items_by_section[section.id],
                children=[build(child) for child in children[section.id]],
            )

        return RubricFormResponse(
            **RubricVersionResponse.model_validate(version).model_dump(),
            categories=[
                RubricFormCategory(
                    **RubricCategoryResponse.model_validate(category).model_dump(),
                    sections=[
                        build(section)
                        for section in children[None]
                        if section.category_id == category.id
                    ],
                )
                for category in categories
            ],
        )

    # --- categories ---------------------------------------------------------------

    def list_categories(self, version_id: int) -> ListResponse[RubricCategoryResponse]:
        self._require_version(version_id)
        items = [
            RubricCategoryResponse.model_validate(category)
            for category in self.rubric_dao.list_categories(version_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_category(
        self, version_id: int, data: RubricCategoryCreateRequest
    ) -> RubricCategoryResponse:
        self._require_version(version_id)
        self._require_unlocked(version_id)
        if any(c.code == data.code for c in self.rubric_dao.list_categories(version_id)):
            raise ConflictError("Category code already used in this version")
        category = self._add(RubricCategory(version_id=version_id, **data.model_dump()))
        return RubricCategoryResponse.model_validate(category)

    # --- sections -----------------------------------------------------------------

    def list_sections(self, category_id: int) -> ListResponse[RubricSectionResponse]:
        self._require_category(category_id)
        items = [
            RubricSectionResponse.model_validate(section)
            for section in self.rubric_dao.list_sections(category_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_section(
        self, category_id: int, data: RubricSectionCreateRequest
    ) -> RubricSectionResponse:
        category = self._require_category(category_id)
        self._require_unlocked(category.version_id)
        if data.parent_id is not None:
            self._check_parent(category_id, section_id=None, parent_id=data.parent_id)
        section = self._add(RubricSection(category_id=category_id, **data.model_dump()))
        return RubricSectionResponse.model_validate(section)

    def update_section(
        self, section_id: int, data: RubricSectionUpdateRequest
    ) -> RubricSectionResponse:
        section = self._require_section(section_id)
        self._require_unlocked(self._version_of_section(section))
        values = data.model_dump(exclude_unset=True)
        if values.get("parent_id") is not None:
            self._check_parent(section.category_id, section_id, values["parent_id"])
        return RubricSectionResponse.model_validate(self._update(section, values))

    def delete_section(self, section_id: int) -> None:
        section = self._require_section(section_id)
        self._require_unlocked(self._version_of_section(section))
        if self.rubric_dao.section_is_in_use(section_id):
            raise ConflictError("Delete the section's items and sub-sections first")
        self.rubric_dao.delete(section)

    # --- items --------------------------------------------------------------------

    def list_items(self, section_id: int) -> ListResponse[RubricItemResponse]:
        self._require_section(section_id)
        items = [
            RubricItemResponse.model_validate(item)
            for item in self.rubric_dao.list_items(section_id)
        ]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def create_item(self, section_id: int, data: RubricItemCreateRequest) -> RubricItemResponse:
        section = self._require_section(section_id)
        self._require_unlocked(self._version_of_section(section))
        values = data.model_dump(exclude={"field_schema"})
        item = self._add(
            RubricItem(
                section_id=section_id,
                field_schema=_field_schema_json(data.field_schema),
                **values,
            )
        )
        return RubricItemResponse.model_validate(item)

    def update_item(self, item_id: int, data: RubricItemUpdateRequest) -> RubricItemResponse:
        item = self._require_item(item_id)
        values = data.model_dump(exclude_unset=True, exclude={"field_schema"})
        if "field_schema" in data.model_fields_set:
            values["field_schema"] = _field_schema_json(data.field_schema)

        section = self._require_section(item.section_id)
        if self.rubric_dao.is_version_used_by_round(self._version_of_section(section)):
            if set(values) - {"is_active"}:
                raise ConflictError(f"{LOCKED} (only is_active can change)")
        else:
            merged = item.model_dump(include=set(RubricItemFields.model_fields)) | values
            try:
                RubricItemFields.model_validate(merged)
            except ValidationError as exc:
                raise BadRequestError(_validation_message(exc)) from exc
        return RubricItemResponse.model_validate(self._update(item, values))

    def delete_item(self, item_id: int) -> None:
        item = self._require_item(item_id)
        self._require_unlocked(self._version_of_section(self._require_section(item.section_id)))
        if self.rubric_dao.item_has_entries(item_id):
            raise ConflictError("Item is used by submission entries; set is_active=false instead")
        self.rubric_dao.delete(item)

    # --- helpers ------------------------------------------------------------------

    def _require_version(self, version_id: int) -> RubricVersion:
        version = self.rubric_dao.get_version(version_id)
        if version is None:
            raise NotFoundError("Rubric version not found")
        return version

    def _require_category(self, category_id: int) -> RubricCategory:
        category = self.rubric_dao.get_category(category_id)
        if category is None:
            raise NotFoundError("Rubric category not found")
        return category

    def _require_section(self, section_id: int) -> RubricSection:
        section = self.rubric_dao.get_section(section_id)
        if section is None:
            raise NotFoundError("Rubric section not found")
        return section

    def _require_item(self, item_id: int) -> RubricItem:
        item = self.rubric_dao.get_item(item_id)
        if item is None:
            raise NotFoundError("Rubric item not found")
        return item

    def _version_of_section(self, section: RubricSection) -> int:
        return self._require_category(section.category_id).version_id

    def _require_unlocked(self, version_id: int) -> None:
        if self.rubric_dao.is_version_used_by_round(version_id):
            raise ConflictError(LOCKED)

    def _check_parent(self, category_id: int, section_id: int | None, parent_id: int) -> None:
        parent = self.rubric_dao.get_section(parent_id)
        if parent is None or parent.category_id != category_id:
            raise BadRequestError("parent_id must be a section of the same category")
        # walk up from the new parent: reaching this section again would make a loop
        seen: set[int] = set()
        while parent is not None and parent.id not in seen:
            if parent.id == section_id:
                raise BadRequestError("A section cannot be inside itself")
            seen.add(parent.id)
            parent = self.rubric_dao.get_section(parent.parent_id) if parent.parent_id else None

    def _copy_structure(self, source_version_id: int, target_version_id: int) -> None:
        section_map: dict[int, int] = {}
        sections = self.rubric_dao.list_sections_of_version(source_version_id)
        for category in self.rubric_dao.list_categories(source_version_id):
            new_category = self._add(
                RubricCategory(
                    **category.model_dump(exclude={"id", "version_id"}),
                    version_id=target_version_id,
                )
            )
            for section in (s for s in sections if s.category_id == category.id):
                new_section = self._add(
                    RubricSection(
                        **section.model_dump(exclude={"id", "category_id", "parent_id"}),
                        category_id=new_category.id,
                    )
                )
                section_map[section.id] = new_section.id
        # parents may come after their children in the list, so link them afterwards
        for section in sections:
            if section.parent_id is not None and section.parent_id in section_map:
                copy = self.rubric_dao.get_section(section_map[section.id])
                self.rubric_dao.update(copy, {"parent_id": section_map[section.parent_id]})
        for item in self.rubric_dao.list_items_of_version(source_version_id):
            self._add(
                RubricItem(
                    **item.model_dump(exclude={"id", "section_id"}),
                    section_id=section_map[item.section_id],
                )
            )

    def _add[T: (RubricVersion, RubricCategory, RubricSection, RubricItem)](self, entity: T) -> T:
        try:
            return self.rubric_dao.add(entity)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Code already used") from exc
            raise

    def _update[T: (RubricVersion, RubricCategory, RubricSection, RubricItem)](
        self, entity: T, values: Mapping[str, Any]
    ) -> T:
        try:
            return self.rubric_dao.update(entity, values)
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("Code already used") from exc
            raise
