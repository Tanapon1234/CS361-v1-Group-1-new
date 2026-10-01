"""DTOs for profile image / CV upload (presigned S3 URL flow).

1. `POST .../presign`  -> server returns a presigned S3 URL
2. client uploads the file straight to S3
3. `POST .../complete` -> server saves it on the lecturer (profile_image_url / cv_url)
"""

from datetime import datetime

from pydantic import Field

from app.v2.dtos.base import RequestDTO, ResponseDTO


class UploadPresignRequest(RequestDTO):
    content_type: str = Field(min_length=1, max_length=127, examples=["image/jpeg"])
    size_bytes: int = Field(gt=0)


class UploadPresignResponse(ResponseDTO):
    upload_url: str
    # Form fields for a presigned POST; stays empty if you choose presigned PUT
    fields: dict[str, str] = Field(default_factory=dict)
    object_key: str
    expires_at: datetime


class UploadCompleteRequest(RequestDTO):
    object_key: str = Field(min_length=1, max_length=1024)


class FileDownloadResponse(ResponseDTO):
    download_url: str
    expires_at: datetime
