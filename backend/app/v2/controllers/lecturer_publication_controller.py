"""Publications authored by one lecturer."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.v2.controllers.params import LecturerId
from app.v2.dependencies import PublicationServiceDep
from app.v2.dtos.common import PageResponse
from app.v2.dtos.publication_dto import PublicationListQuery, PublicationResponse

router = APIRouter(prefix="/lecturers/{lecturer_id}/publications", tags=["publications"])


@router.get("")
def list_lecturer_publications(
    lecturer_id: LecturerId,
    query: Annotated[PublicationListQuery, Query()],
    service: PublicationServiceDep,
) -> PageResponse[PublicationResponse]:
    return service.list_lecturer_publications(lecturer_id, query)
