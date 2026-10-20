"""Talk to the /api/v2 endpoints from a script, either in-process or over HTTP.

In-process (default) runs the app against the database in `.env`, so nothing has to be
started first. `--base-url` sends the same requests to a running backend instead (local
server or the deployed API). Going through the API keeps every validation, score and
workflow rule the same as when a person enters the data.
"""

import argparse
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx2

V2 = "/api/v2"


class ApiError(RuntimeError):
    pass


def add_target_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        help="Running backend, e.g. http://localhost:8000. Default: in-process with .env",
    )


# Scripts act as admin through the dev headers (docs/v2/permissions.md); the target
# backend must not run with ENVIRONMENT=prod. `as_()` adds the lecturer to act as.
SCRIPT_HEADERS = {"X-Dev-Roles": "admin"}


@contextmanager
def open_api(base_url: str | None) -> Iterator[httpx2.Client]:
    logging.getLogger("httpx2").setLevel(logging.WARNING)  # no line per request
    if base_url:
        with httpx2.Client(
            base_url=base_url.rstrip("/"), timeout=30, headers=SCRIPT_HEADERS
        ) as client:
            yield client
        return

    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app(), headers=SCRIPT_HEADERS) as client:
        yield client


def as_(lecturer_id: str) -> dict[str, str]:
    """Act as this lecturer (X-Lecturer-Id, until Cognito)."""
    return {"X-Lecturer-Id": lecturer_id}


def call(
    api: httpx2.Client,
    method: str,
    path: str,
    *,
    expect: tuple[int, ...] = (200, 201, 204),
    **kwargs: Any,
) -> Any:
    response = api.request(method, f"{V2}{path}", **kwargs)
    if response.status_code not in expect:
        raise ApiError(f"{method} {path} -> {response.status_code}: {response.text}")
    return response.json() if response.content else None


def find_one(api: httpx2.Client, path: str, key: str, value: str, **params: Any) -> Any | None:
    """First item of a list endpoint whose `key` equals `value` (case-insensitive)."""
    page = call(api, "GET", path, params={"limit": 100, **params})
    wanted = value.casefold()
    return next(
        (item for item in page["items"] if str(item[key]).casefold() == wanted),
        None,
    )


def find_lecturer(api: httpx2.Client, email: str) -> Any | None:
    return find_one(api, "/lecturers", "email", email, q=email)


def ensure_master(api: httpx2.Client, path: str, key: str, value: str, id_key: str) -> int:
    """Id of a master row (research interest, expertise...) with this name, created if needed."""
    found = find_one(api, path, key, value, q=value[:100])
    if found is None:
        found = call(api, "POST", path, json={key: value})
    return found[id_key]
