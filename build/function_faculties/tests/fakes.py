"""In-memory fakes so unit tests never touch AWS."""

from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","lambda")))


class FakeClientError(Exception):
    """Mimics botocore.exceptions.ClientError (same ``response`` shape)."""

    def __init__(self, code: str, message: str = "fake error") -> None:
        super().__init__(f"{code}: {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


class FakeS3Client:
    """Minimal read-only S3 double. Exposes get_object only, on purpose."""

    def __init__(self, objects=None, error=None):
        # objects: {key: str|bytes|obj}
        self.objects = objects or {}
        self.error = error
        self.calls = []

    def get_object(self, Bucket, Key):  # noqa: N803 - boto3 signature
        self.calls.append((Bucket, Key))
        if self.error is not None:
            raise self.error
        if Key not in self.objects:
            raise FakeClientError("NoSuchKey", "The specified key does not exist.")
        body = self.objects[Key]
        if not isinstance(body, (str, bytes)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode("utf-8")
        return {"Body": io.BytesIO(body)}


def api_event(path, method="GET", path_parameters=None, stage="prod"):
    """REST API (payload v1) style event."""
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_parameters,
        "requestContext": {"stage": stage, "httpMethod": method, "path": f"/{stage}{path}"},
    }


def http_api_event(raw_path, method="GET", path_parameters=None):
    """HTTP API (payload v2) style event."""
    return {
        "version": "2.0",
        "rawPath": raw_path,
        "pathParameters": path_parameters,
        "requestContext": {"stage": "$default", "http": {"method": method, "path": raw_path}},
    }
