"""Read-only S3 access for the serving prefix.

Security boundary: this module exposes **only** ``get_object``.  No write,
delete or copy API is imported, referenced or reachable from any code path,
and every key is forced under ``SERVING_PREFIX`` before the call is made.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SAFE_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]*$")
_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchBucket", "404", "NotFound"}


class S3RepositoryError(Exception):
    """Base class for storage failures."""


class ObjectNotFoundError(S3RepositoryError):
    """S3 NoSuchKey / 404."""


class ObjectAccessError(S3RepositoryError):
    """AccessDenied, throttling, network or any other S3 service error."""


class InvalidJsonError(S3RepositoryError):
    """Object exists but its body is not valid UTF-8 JSON."""


def _error_code(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = response.get("Error", {}).get("Code")
        if code:
            return str(code)
    return exc.__class__.__name__


class S3Repository:
    """Fetch JSON documents from ``s3://<bucket>/<prefix>/...`` (read only)."""

    def __init__(self, bucket: str, prefix: str = "serving", client: Optional[Any] = None) -> None:
        if not bucket:
            raise ValueError("bucket name is required")
        self.bucket = bucket
        self.prefix = (prefix or "").strip("/")
        self._client = client

    @property
    def client(self):
        if self._client is None:  # pragma: no cover - exercised on Lambda only
            import boto3

            self._client = boto3.client("s3")
        return self._client

    def build_key(self, relative_key: str) -> str:
        """Join ``relative_key`` under the serving prefix, refusing escapes."""
        if not relative_key or relative_key.startswith("/"):
            raise ObjectAccessError("invalid_relative_key")

        key = f"{self.prefix}/{relative_key}" if self.prefix else relative_key

        if ".." in key or "\\" in key or "//" in key or not _SAFE_KEY_PATTERN.match(key):
            raise ObjectAccessError("unsafe_key")
        if self.prefix and not key.startswith(f"{self.prefix}/"):
            raise ObjectAccessError("key_outside_serving_prefix")
        return key

    def get_json(self, relative_key: str) -> Any:
        key = self.build_key(relative_key)
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            raw = response["Body"].read()
        except Exception as exc:  # noqa: BLE001 - normalised below
            code = _error_code(exc)
            if code in _NOT_FOUND_CODES:
                logger.info("s3_object_not_found key=%s", key)
                raise ObjectNotFoundError(key) from exc
            # Only the error *code* is logged - never credentials or payloads.
            logger.error("s3_access_error key=%s error_code=%s", key, code)
            raise ObjectAccessError(code) from exc

        if isinstance(raw, str):
            raw = raw.encode("utf-8")

        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            logger.error("s3_invalid_json key=%s error_type=%s", key, exc.__class__.__name__)
            raise InvalidJsonError(key) from exc
