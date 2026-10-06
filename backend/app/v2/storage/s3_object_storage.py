"""S3 implementation of ObjectStorage (boto3).

Credentials come from the usual AWS chain (env vars, profile, or the Lambda/ECS role).
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.v2.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)


class S3ObjectStorage(ObjectStorage):
    def __init__(self, *, bucket_name: str, region: str, client: Any = None) -> None:
        self.bucket_name = bucket_name
        self.region = region
        # SigV4 so presigned URLs work in every region; the client is thread-safe
        self.client = client or boto3.client(
            "s3", region_name=region, config=Config(signature_version="s3v4")
        )

    def create_presigned_upload(
        self, *, key: str, content_type: str, max_size_bytes: int, expires_in_seconds: int
    ) -> PresignedUpload:
        post = self.client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, max_size_bytes],
            ],
            ExpiresIn=expires_in_seconds,
        )
        return PresignedUpload(
            url=post["url"],
            fields=post["fields"],
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def create_presigned_download(
        self, *, key: str, file_name: str, expires_in_seconds: int
    ) -> PresignedDownload:
        # RFC 6266: filename* carries non-ASCII (Thai) names
        disposition = f"attachment; filename*=UTF-8''{quote(file_name)}"
        url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
                "ResponseContentDisposition": disposition,
            },
            ExpiresIn=expires_in_seconds,
        )
        return PresignedDownload(
            url=url, expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds)
        )

    def head_object(self, key: str) -> StoredObject | None:
        try:
            head = self.client.head_object(Bucket=self.bucket_name, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return StoredObject(
            key=key, size_bytes=head["ContentLength"], content_type=head.get("ContentType")
        )

    def delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=key)
