"""Master list of expertise."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import ExpertiseId
from app.v2.dependencies import ExpertiseServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.expertise_dto import (
    ExpertiseCreateRequest,
    ExpertiseListQuery,
    ExpertiseResponse,
    ExpertiseUpdateRequest,
)

router = APIRouter(prefix="/expertise", tags=["expertise"])


@router.get("")
def list_expertise(
    query: Annotated[ExpertiseListQuery, Query()], service: ExpertiseServiceDep
) -> PageResponse[ExpertiseResponse]:
    return service.list_expertise(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_expertise(
    data: ExpertiseCreateRequest, service: ExpertiseServiceDep
) -> ExpertiseResponse:
    return service.create_expertise(data)


@router.get("/{expertise_id}")
def get_expertise(expertise_id: ExpertiseId, service: ExpertiseServiceDep) -> ExpertiseResponse:
    return service.get_expertise(expertise_id)


@router.patch("/{expertise_id}")
def update_expertise(
    expertise_id: ExpertiseId, data: ExpertiseUpdateRequest, service: ExpertiseServiceDep
) -> ExpertiseResponse:
    return service.update_expertise(expertise_id, data)


@router.delete("/{expertise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expertise(expertise_id: ExpertiseId, service: ExpertiseServiceDep) -> None:
    service.delete_expertise(expertise_id)
