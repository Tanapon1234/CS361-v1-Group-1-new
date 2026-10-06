from fastapi import APIRouter, status

from app.v2.controllers.params import LecturerId
from app.v2.dependencies import LecturerFileServiceDep
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.lecturer_file_dto import (
    UploadCompleteRequest,
    UploadPresignRequest,
    UploadPresignResponse,
)

router = APIRouter(prefix="/lecturers/{lecturer_id}/profile-image", tags=["lecturer-files"])


@router.post("/presign")
def presign_profile_image_upload(
    lecturer_id: LecturerId, data: UploadPresignRequest, service: LecturerFileServiceDep
) -> UploadPresignResponse:
    """Step 1: get a presigned URL to upload the image directly to S3."""
    return service.create_profile_image_upload(lecturer_id, data)


@router.post("/complete")
def complete_profile_image_upload(
    lecturer_id: LecturerId, data: UploadCompleteRequest, service: LecturerFileServiceDep
) -> LecturerResponse:
    """Step 2: after uploading to S3, save it as the lecturer's profile image."""
    return service.complete_profile_image_upload(lecturer_id, data)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_image(lecturer_id: LecturerId, service: LecturerFileServiceDep) -> None:
    service.delete_profile_image(lecturer_id)
