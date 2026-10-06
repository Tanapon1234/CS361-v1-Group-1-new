"""S3ObjectStorage without network: presigning is local, head/delete use a stubbed client."""

import boto3
import pytest
from botocore.stub import Stubber

from app.v2.storage.s3_object_storage import S3ObjectStorage


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch) -> S3ObjectStorage:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    client = boto3.client("s3", region_name="ap-southeast-1")
    return S3ObjectStorage(bucket_name="bucket", region="ap-southeast-1", client=client)


def test_presigned_upload_limits_type_and_size(storage: S3ObjectStorage) -> None:
    upload = storage.create_presigned_upload(
        key="a/b.pdf", content_type="application/pdf", max_size_bytes=1000, expires_in_seconds=60
    )

    assert upload.fields["key"] == "a/b.pdf"
    assert upload.fields["Content-Type"] == "application/pdf"
    assert "policy" in upload.fields


def test_presigned_download_keeps_a_thai_file_name(storage: S3ObjectStorage) -> None:
    download = storage.create_presigned_download(
        key="a/b.pdf", file_name="คำสั่ง.pdf", expires_in_seconds=60
    )

    assert "response-content-disposition=attachment" in download.url
    assert "%25E0%25B8" in download.url  # the Thai name, percent-encoded twice in the query


def test_head_object_returns_none_when_missing(storage: S3ObjectStorage) -> None:
    with Stubber(storage.client) as stub:
        stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
        assert storage.head_object("missing") is None


def test_head_object_returns_size(storage: S3ObjectStorage) -> None:
    with Stubber(storage.client) as stub:
        stub.add_response(
            "head_object",
            {"ContentLength": 42, "ContentType": "application/pdf"},
            {"Bucket": "bucket", "Key": "a"},
        )
        stored = storage.head_object("a")

    assert stored is not None
    assert (stored.size_bytes, stored.content_type) == (42, "application/pdf")
