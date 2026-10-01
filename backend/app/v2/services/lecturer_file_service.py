"""Profile image and CV upload (presigned S3 URLs).

Flow: presign -> client uploads to S3 -> complete saves the file on the lecturer
(`lecturer.profile_image_url` / `lecturer.cv_url`). Size limits are in Settings
(PROFILE_IMAGE_MAX_BYTES, CV_MAX_BYTES). Allowed file types are up to you.
"""

from uuid import UUID

from app.core.config import Settings
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.lecturer_file_dto import (
    FileDownloadResponse,
    UploadCompleteRequest,
    UploadPresignRequest,
    UploadPresignResponse,
)
from app.v2.storage.object_storage import ObjectStorage


class LecturerFileService:
    def __init__(
        self, lecturer_dao: LecturerDAO, storage: ObjectStorage, settings: Settings
    ) -> None:
        self.lecturer_dao = lecturer_dao
        self.storage = storage
        self.settings = settings

    # --- profile image -----------------------------------------------------------

    def create_profile_image_upload(
        self, lecturer_id: UUID, data: UploadPresignRequest
    ) -> UploadPresignResponse:
        raise NotImplementedError  # TODO

    def complete_profile_image_upload(
        self, lecturer_id: UUID, data: UploadCompleteRequest
    ) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def delete_profile_image(self, lecturer_id: UUID) -> None:
        raise NotImplementedError  # TODO

    # --- CV ----------------------------------------------------------------------

    def create_cv_upload(
        self, lecturer_id: UUID, data: UploadPresignRequest
    ) -> UploadPresignResponse:
        raise NotImplementedError  # TODO

    def complete_cv_upload(
        self, lecturer_id: UUID, data: UploadCompleteRequest
    ) -> LecturerResponse:
        raise NotImplementedError  # TODO

    def get_cv(self, lecturer_id: UUID) -> FileDownloadResponse:
        raise NotImplementedError  # TODO

    def delete_cv(self, lecturer_id: UUID) -> None:
        raise NotImplementedError  # TODO
