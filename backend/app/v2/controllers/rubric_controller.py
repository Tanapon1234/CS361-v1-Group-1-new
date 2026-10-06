from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import (
    RubricCategoryId,
    RubricItemId,
    RubricSectionId,
    RubricVersionId,
)
from app.v2.dependencies import RubricServiceDep
from app.v2.dtos.common import ListResponse, PageQuery, PageResponse
from app.v2.dtos.rubric_dto import (
    RubricCategoryCreateRequest,
    RubricCategoryResponse,
    RubricFormResponse,
    RubricItemCreateRequest,
    RubricItemResponse,
    RubricItemUpdateRequest,
    RubricSectionCreateRequest,
    RubricSectionResponse,
    RubricSectionUpdateRequest,
    RubricVersionCreateRequest,
    RubricVersionResponse,
    RubricVersionUpdateRequest,
)

router = APIRouter(tags=["rubric"])

# --- versions ---------------------------------------------------------------------


@router.get("/rubric-versions")
def list_rubric_versions(
    query: Annotated[PageQuery, Query()], service: RubricServiceDep
) -> PageResponse[RubricVersionResponse]:
    return service.list_versions(query)


@router.post("/rubric-versions", status_code=status.HTTP_201_CREATED)
def create_rubric_version(
    data: RubricVersionCreateRequest, service: RubricServiceDep
) -> RubricVersionResponse:
    """Send `source_version_id` to copy every category, section and item of that version."""
    return service.create_version(data)


@router.get("/rubric-versions/{version_id}")
def get_rubric_version(
    version_id: RubricVersionId, service: RubricServiceDep
) -> RubricVersionResponse:
    return service.get_version(version_id)


@router.patch("/rubric-versions/{version_id}")
def update_rubric_version(
    version_id: RubricVersionId, data: RubricVersionUpdateRequest, service: RubricServiceDep
) -> RubricVersionResponse:
    """409 once an evaluation round uses the version."""
    return service.update_version(version_id, data)


@router.get("/rubric-versions/{version_id}/form")
def get_rubric_form(version_id: RubricVersionId, service: RubricServiceDep) -> RubricFormResponse:
    """The whole rubric in one tree: category -> section -> (sub-section) -> item."""
    return service.get_form(version_id)


# --- categories -------------------------------------------------------------------


@router.get("/rubric-versions/{version_id}/categories")
def list_rubric_categories(
    version_id: RubricVersionId, service: RubricServiceDep
) -> ListResponse[RubricCategoryResponse]:
    return service.list_categories(version_id)


@router.post("/rubric-versions/{version_id}/categories", status_code=status.HTTP_201_CREATED)
def create_rubric_category(
    version_id: RubricVersionId, data: RubricCategoryCreateRequest, service: RubricServiceDep
) -> RubricCategoryResponse:
    return service.create_category(version_id, data)


# --- sections ---------------------------------------------------------------------


@router.get("/rubric-categories/{category_id}/sections")
def list_rubric_sections(
    category_id: RubricCategoryId, service: RubricServiceDep
) -> ListResponse[RubricSectionResponse]:
    return service.list_sections(category_id)


@router.post("/rubric-categories/{category_id}/sections", status_code=status.HTTP_201_CREATED)
def create_rubric_section(
    category_id: RubricCategoryId, data: RubricSectionCreateRequest, service: RubricServiceDep
) -> RubricSectionResponse:
    return service.create_section(category_id, data)


@router.patch("/rubric-sections/{section_id}")
def update_rubric_section(
    section_id: RubricSectionId, data: RubricSectionUpdateRequest, service: RubricServiceDep
) -> RubricSectionResponse:
    return service.update_section(section_id, data)


@router.delete("/rubric-sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric_section(section_id: RubricSectionId, service: RubricServiceDep) -> None:
    service.delete_section(section_id)


# --- items ------------------------------------------------------------------------


@router.get("/rubric-sections/{section_id}/items")
def list_rubric_items(
    section_id: RubricSectionId, service: RubricServiceDep
) -> ListResponse[RubricItemResponse]:
    return service.list_items(section_id)


@router.post("/rubric-sections/{section_id}/items", status_code=status.HTTP_201_CREATED)
def create_rubric_item(
    section_id: RubricSectionId, data: RubricItemCreateRequest, service: RubricServiceDep
) -> RubricItemResponse:
    return service.create_item(section_id, data)


@router.patch("/rubric-items/{item_id}")
def update_rubric_item(
    item_id: RubricItemId, data: RubricItemUpdateRequest, service: RubricServiceDep
) -> RubricItemResponse:
    """Change the weight, or turn the item off with `{"is_active": false}`."""
    return service.update_item(item_id, data)


@router.delete("/rubric-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric_item(item_id: RubricItemId, service: RubricServiceDep) -> None:
    """409 if any entry uses the item."""
    service.delete_item(item_id)
