"""Profile image and CV upload (presigned S3 URLs).

Flow: presign -> client uploads to S3 -> complete saves the file on the lecturer
(`lecturer.profile_image_url` / `lecturer.cv_url`). Size limits and allowed types are in
Settings (PROFILE_IMAGE_*, CV_*).

Both columns hold the S3 object key of an uploaded file. Rows migrated from V1 may still
hold an external http(s) URL instead; those are handed back as they are.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from typing import Literal
from uuid import UUID, uuid4

from app.core.config import Settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.lecturer_file_dto import (
    FileDownloadResponse,
    UploadCompleteRequest,
    UploadPresignRequest,
    UploadPresignResponse,
)
from app.v2.models.lecturer import Lecturer
from app.v2.storage.object_storage import ObjectStorage

_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


@dataclass(frozen=True, slots=True)
class _FileKind:
    column: Literal["profile_image_url", "cv_url"]
    folder: str
    label: str
    allowed_types: list[str]
    max_bytes: int


class LecturerFileService:
    def __init__(
        self, lecturer_dao: LecturerDAO, storage: ObjectStorage, settings: Settings
    ) -> None:
        self.lecturer_dao = lecturer_dao
        self.storage = storage
        self.settings = settings
        self._image = _FileKind(
            column="profile_image_url",
            folder="profile-image",
            label="Profile image",
            allowed_types=settings.profile_image_allowed_mime_types,
            max_bytes=settings.profile_image_max_bytes,
        )
        self._cv = _FileKind(
            column="cv_url",
            folder="cv",
            label="CV",
            allowed_types=settings.cv_allowed_mime_types,
            max_bytes=settings.cv_max_bytes,
        )

    # --- profile image -----------------------------------------------------------

    def create_profile_image_upload(
        self, lecturer_id: UUID, data: UploadPresignRequest
    ) -> UploadPresignResponse:
        return self._create_upload(lecturer_id, data, self._image)

    def complete_profile_image_upload(
        self, lecturer_id: UUID, data: UploadCompleteRequest
    ) -> LecturerResponse:
        return self._complete_upload(lecturer_id, data, self._image)

    def get_profile_image(self, lecturer_id: UUID) -> FileDownloadResponse:
        return self._download(lecturer_id, self._image)

    def delete_profile_image(self, lecturer_id: UUID) -> None:
        self._delete(lecturer_id, self._image)

    # --- CV ----------------------------------------------------------------------

    def create_cv_upload(
        self, lecturer_id: UUID, data: UploadPresignRequest
    ) -> UploadPresignResponse:
        return self._create_upload(lecturer_id, data, self._cv)

    def complete_cv_upload(
        self, lecturer_id: UUID, data: UploadCompleteRequest
    ) -> LecturerResponse:
        return self._complete_upload(lecturer_id, data, self._cv)

    def get_cv(self, lecturer_id: UUID) -> FileDownloadResponse:
        return self._download(lecturer_id, self._cv)

    def delete_cv(self, lecturer_id: UUID) -> None:
        self._delete(lecturer_id, self._cv)

    # --- shared ------------------------------------------------------------------

    def _create_upload(
        self, lecturer_id: UUID, data: UploadPresignRequest, kind: _FileKind
    ) -> UploadPresignResponse:
        self._require_lecturer(lecturer_id)
        self._check_file(data.content_type, data.size_bytes, kind)

        extension = _EXTENSIONS.get(data.content_type, "")
        key = f"{self._prefix(lecturer_id, kind)}{uuid4().hex}{extension}"
        upload = self.storage.create_presigned_upload(
            key=key,
            content_type=data.content_type,
            max_size_bytes=data.size_bytes,
            expires_in_seconds=self.settings.s3_presign_expires_seconds,
        )
        return UploadPresignResponse(
            upload_url=upload.url,
            fields=upload.fields,
            object_key=key,
            expires_at=upload.expires_at,
        )

    def _complete_upload(
        self, lecturer_id: UUID, data: UploadCompleteRequest, kind: _FileKind
    ) -> LecturerResponse:
        lecturer = self._require_lecturer(lecturer_id)
        if not data.object_key.startswith(self._prefix(lecturer_id, kind)):
            raise BadRequestError(f"object_key is not a {kind.label} upload of this lecturer")

        stored = self.storage.head_object(data.object_key)
        if stored is None:
            raise BadRequestError("The file has not been uploaded to storage yet")
        self._check_file(stored.content_type or "", stored.size_bytes, kind)

        previous = getattr(lecturer, kind.column)
        updated = self.lecturer_dao.update(lecturer, {kind.column: data.object_key})
        if previous != data.object_key and self._is_stored_key(previous, lecturer_id, kind):
            self.storage.delete_object(previous)
        return LecturerResponse.model_validate(updated)

    def _download(self, lecturer_id: UUID, kind: _FileKind) -> FileDownloadResponse:
        lecturer = self._require_lecturer(lecturer_id)
        value = getattr(lecturer, kind.column)
        if not value:
            raise NotFoundError(f"{kind.label} not found")

        if not self._is_stored_key(value, lecturer_id, kind):
            # External URL from V1: nothing to sign
            expires_at = datetime.now(UTC) + timedelta(
                seconds=self.settings.s3_presign_expires_seconds
            )
            return FileDownloadResponse(download_url=value, expires_at=expires_at)

        name = lecturer.name_en or lecturer.name_th
        extension = PurePosixPath(value).suffix
        download = self.storage.create_presigned_download(
            key=value,
            file_name=f"{kind.folder}-{name}{extension}",
            expires_in_seconds=self.settings.s3_presign_expires_seconds,
        )
        return FileDownloadResponse(download_url=download.url, expires_at=download.expires_at)

    def _delete(self, lecturer_id: UUID, kind: _FileKind) -> None:
        lecturer = self._require_lecturer(lecturer_id)
        value = getattr(lecturer, kind.column)
        if not value:
            raise NotFoundError(f"{kind.label} not found")

        self.lecturer_dao.update(lecturer, {kind.column: None})
        if self._is_stored_key(value, lecturer_id, kind):
            self.storage.delete_object(value)

    def _check_file(self, content_type: str, size_bytes: int, kind: _FileKind) -> None:
        if content_type not in kind.allowed_types:
            allowed = ", ".join(kind.allowed_types)
            raise BadRequestError(f"{kind.label} must be one of: {allowed}")
        if size_bytes > kind.max_bytes:
            raise BadRequestError(f"{kind.label} is larger than {kind.max_bytes} bytes")

    def _require_lecturer(self, lecturer_id: UUID) -> Lecturer:
        lecturer = self.lecturer_dao.get_by_id(lecturer_id)
        if lecturer is None:
            raise NotFoundError("Lecturer not found")
        return lecturer

    @staticmethod
    def _prefix(lecturer_id: UUID, kind: _FileKind) -> str:
        return f"lecturers/{lecturer_id}/{kind.folder}/"

    def _is_stored_key(self, value: str | None, lecturer_id: UUID, kind: _FileKind) -> bool:
        return bool(value) and value.startswith(self._prefix(lecturer_id, kind))
