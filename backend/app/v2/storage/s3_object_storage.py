"""S3 implementation of ObjectStorage (boto3).

Hints:
    client = boto3.client("s3", region_name=region)   # create once; clients are thread-safe
    client.generate_presigned_post(
        Bucket=..., Key=key, ExpiresIn=...,
        Fields={"Content-Type": content_type},
        Conditions=[{"Content-Type": content_type}, ["content-length-range", 1, max_size_bytes]],
    )
    client.generate_presigned_url("get_object", Params={..., "ResponseContentDisposition": ...})
    client.head_object(...)   # raises ClientError with code "404" when missing
    client.delete_object(...)
"""

from app.v2.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)


class S3ObjectStorage(ObjectStorage):
    def __init__(self, *, bucket_name: str, region: str) -> None:
        self.bucket_name = bucket_name
        self.region = region

    def create_presigned_upload(
        self, *, key: str, content_type: str, max_size_bytes: int, expires_in_seconds: int
    ) -> PresignedUpload:
        raise NotImplementedError

    def create_presigned_download(
        self, *, key: str, file_name: str, expires_in_seconds: int
    ) -> PresignedDownload:
        raise NotImplementedError

    def head_object(self, key: str) -> StoredObject | None:
        raise NotImplementedError

    def delete_object(self, key: str) -> None:
        raise NotImplementedError
