"""Fixtures for tests against a real PostgreSQL; see support.py for how to run them."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlmodel import Session, create_engine

from app.core.database import get_session
from app.v2.dependencies import get_actor, get_object_storage
from tests.v2.integration.support import DATABASE_URL, MIGRATIONS, FakeStorage


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    engine = create_engine(DATABASE_URL)  # type: ignore[arg-type]
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cursor:
            for name in (
                "002_lecturer_profile.sql",
                "003_faculty_workload.sql",
                "004_workload_entry_lock.sql",
            ):
                cursor.execute((MIGRATIONS / name).read_text())
        raw.commit()
    finally:
        raw.close()
    yield engine
    engine.dispose()


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def api(app: FastAPI, engine: Engine, storage: FakeStorage) -> Iterator[TestClient]:
    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_object_storage] = lambda: storage
    # The real caller check (dev headers): admin by default, X-Lecturer-Id per request
    app.dependency_overrides.pop(get_actor, None)
    with TestClient(app, headers={"X-Dev-Roles": "admin"}) as client:
        yield client
