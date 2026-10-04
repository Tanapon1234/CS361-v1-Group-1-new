from typing import Annotated

from fastapi import APIRouter, Query, status

from app.v2.controllers.params import PublicationId
from app.v2.dependencies import PublicationServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationListItemResponse,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateRequest,
    PublicationUpdateResponse,
)

router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("")
def list_publications(
    query: Annotated[PublicationListQuery, Query()], service: PublicationServiceDep
) -> PageResponse[PublicationListItemResponse]:
    return service.list_publications(query)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_publication(
    data: PublicationCreateRequest, service: PublicationServiceDep
) -> PublicationListItemResponse:
    return service.create_publication(data)


@router.get("/{publication_id}")
def get_publication(
    publication_id: PublicationId, service: PublicationServiceDep
) -> PublicationListItemResponse:
    return service.get_publication(publication_id)


@router.patch("/{publication_id}")
def update_publication(
    publication_id: PublicationId, data: PublicationUpdateRequest, service: PublicationServiceDep
) -> PublicationUpdateResponse:
    return service.update_publication(publication_id, data)


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(publication_id: PublicationId, service: PublicationServiceDep) -> None:
    service.delete_publication(publication_id)
