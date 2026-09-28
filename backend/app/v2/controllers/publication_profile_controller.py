from fastapi import APIRouter, status

from app.v2.controllers.params import LecturerId, PublicationProfileId
from app.v2.dependencies import PublicationProfileServiceDep
from app.v2.dtos.common import ListResponse
from app.v2.dtos.publication_profile_dto import (
    PublicationProfileCreateRequest,
    PublicationProfileResponse,
    PublicationProfileUpdateRequest,
)

router = APIRouter(
    prefix="/lecturers/{lecturer_id}/publication-profiles", tags=["publication-profiles"]
)


@router.get("")
def list_publication_profiles(
    lecturer_id: LecturerId, service: PublicationProfileServiceDep
) -> ListResponse[PublicationProfileResponse]:
    return service.list_publication_profiles(lecturer_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_publication_profile(
    lecturer_id: LecturerId,
    data: PublicationProfileCreateRequest,
    service: PublicationProfileServiceDep,
) -> PublicationProfileResponse:
    return service.create_publication_profile(lecturer_id, data)


@router.patch("/{publication_profile_id}")
def update_publication_profile(
    lecturer_id: LecturerId,
    publication_profile_id: PublicationProfileId,
    data: PublicationProfileUpdateRequest,
    service: PublicationProfileServiceDep,
) -> PublicationProfileResponse:
    return service.update_publication_profile(lecturer_id, publication_profile_id, data)


@router.delete("/{publication_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication_profile(
    lecturer_id: LecturerId,
    publication_profile_id: PublicationProfileId,
    service: PublicationProfileServiceDep,
) -> None:
    service.delete_publication_profile(lecturer_id, publication_profile_id)
