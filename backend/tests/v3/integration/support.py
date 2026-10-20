"""Helpers for tests that run against a real PostgreSQL (migrations 002-004).

Skipped unless TEST_DATABASE_URL points at a database that may be wiped, e.g.

    createdb cs361_test
    TEST_DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/cs361_test uv run pytest

Never point it at a dev or prod database: every test module drops and recreates the
public schema.
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.v3.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
MIGRATIONS = Path(__file__).parents[4] / "database" / "migrations"

requires_database = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not set")


class FakeStorage(ObjectStorage):
    """In-memory S3: `uploaded` holds the keys a client 'uploaded'."""

    def __init__(self) -> None:
        self.uploaded: dict[str, int] = {}
        self.content_types: dict[str, str] = {}
        self.deleted: list[str] = []

    def create_presigned_upload(
        self, *, key: str, content_type: str, max_size_bytes: int, expires_in_seconds: int
    ) -> PresignedUpload:
        return PresignedUpload(
            url="https://s3.example/upload",
            fields={"key": key, "Content-Type": content_type},
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def create_presigned_download(
        self, *, key: str, file_name: str, expires_in_seconds: int
    ) -> PresignedDownload:
        return PresignedDownload(
            url=f"https://s3.example/{key}",
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def head_object(self, key: str) -> StoredObject | None:
        size = self.uploaded.get(key)
        if size is None:
            return None
        return StoredObject(key=key, size_bytes=size, content_type=self.content_types.get(key))

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)


def as_(lecturer_id: str) -> dict[str, str]:
    return {"X-Lecturer-Id": lecturer_id}


def ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, response.text
    return response.json() if response.content else None
