"""Shared fixtures.

API tests never touch a real database: `get_session` is replaced by a mock, and each
test module replaces the service it needs via `app.dependency_overrides`.

They test the HTTP contract (routing, validation, status codes), so the caller is an
admin: the lecturer in `X-Lecturer-Id`, or a role-only script caller without it, and the
route check / audit (`authorize`) is skipped. Who may call what is tested with the real
caller in tests/v2/test_permissions.py, auditing in tests/v2/integration/.
"""

from collections.abc import Iterator
from typing import Annotated
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.main import create_app
from app.v2.dependencies import authorize, get_actor
from app.v2.security import Actor, Role


def contract_test_actor(x_lecturer_id: Annotated[UUID | None, Header()] = None) -> Actor:
    if x_lecturer_id is None:
        return Actor(None, frozenset({Role.ADMIN}))
    return Actor(x_lecturer_id, frozenset({Role.LECTURER, Role.ADMIN}))


@pytest.fixture
def session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def app(session: MagicMock) -> Iterator[FastAPI]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_actor] = contract_test_actor
    app.dependency_overrides[authorize] = lambda: None
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client
