"""The per-request session commits on success and rolls back on any error."""

from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.core.database import SessionDep
from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import ConflictError

# A throwaway table, independent of any API version's models.
notes = sa.Table("note", sa.MetaData(), sa.Column("body", sa.String, primary_key=True))


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    notes.metadata.create_all(engine)
    monkeypatch.setattr("app.core.database.get_engine", lambda: engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine: Engine) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/ok", status_code=201)
    def create_ok(session: SessionDep) -> None:
        session.execute(notes.insert().values(body="committed"))

    @app.post("/fail")
    def create_then_fail(session: SessionDep) -> None:
        session.execute(notes.insert().values(body="rolled-back"))
        raise ConflictError("boom")

    return TestClient(app)


def stored_bodies(engine: Engine) -> list[str]:
    with Session(engine) as session:
        return list(session.execute(sa.select(notes.c.body)).scalars())


def test_commits_when_request_succeeds(client: TestClient, engine: Engine) -> None:
    response = client.post("/ok")

    assert response.status_code == 201
    assert stored_bodies(engine) == ["committed"]


def test_rolls_back_when_request_fails(client: TestClient, engine: Engine) -> None:
    response = client.post("/fail")

    assert response.status_code == 409
    assert stored_bodies(engine) == []
