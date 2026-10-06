"""Object storage contract (S3 in dev/prod, mocks in tests)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    url: str
    fields: dict[str, str]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PresignedDownload:
    url: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class StoredObject:
    key: str
    size_bytes: int
    content_type: str | None


class ObjectStorage(ABC):
    @abstractmethod
    def create_presigned_upload(
        self, *, key: str, content_type: str, max_size_bytes: int, expires_in_seconds: int
    ) -> PresignedUpload:
        """Presigned POST that only accepts `content_type` and at most `max_size_bytes`."""

    @abstractmethod
    def create_presigned_download(
        self, *, key: str, file_name: str, expires_in_seconds: int
    ) -> PresignedDownload:
        """Presigned GET that downloads the object as `file_name`."""

    @abstractmethod
    def head_object(self, key: str) -> StoredObject | None:
        """Return object metadata, or None if the object does not exist."""

    @abstractmethod
    def delete_object(self, key: str) -> None: ...
