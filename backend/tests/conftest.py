"""Shared fixtures.

API tests never touch a real database: `get_session` is replaced by a mock, and each
test module replaces the service it needs via `app.dependency_overrides`.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.main import create_app


@pytest.fixture
def session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def app(session: MagicMock) -> Iterator[FastAPI]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client
