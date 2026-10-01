from fastapi import APIRouter, status

from app.v2.controllers.params import LecturerId
from app.v2.dependencies import LecturerFileServiceDep
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.lecturer_file_dto import (
    FileDownloadResponse,
    UploadCompleteRequest,
    UploadPresignRequest,
    UploadPresignResponse,
)

router = APIRouter(prefix="/lecturers/{lecturer_id}/cv", tags=["lecturer-files"])


@router.post("/presign")
def presign_cv_upload(
    lecturer_id: LecturerId, data: UploadPresignRequest, service: LecturerFileServiceDep
) -> UploadPresignResponse:
    """Step 1: get a presigned URL to upload the CV directly to S3."""
    return service.create_cv_upload(lecturer_id, data)


@router.post("/complete")
def complete_cv_upload(
    lecturer_id: LecturerId, data: UploadCompleteRequest, service: LecturerFileServiceDep
) -> LecturerResponse:
    """Step 2: after uploading to S3, save it as the lecturer's CV."""
    return service.complete_cv_upload(lecturer_id, data)


@router.get("")
def get_cv(lecturer_id: LecturerId, service: LecturerFileServiceDep) -> FileDownloadResponse:
    return service.get_cv(lecturer_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_cv(lecturer_id: LecturerId, service: LecturerFileServiceDep) -> None:
    service.delete_cv(lecturer_id)
