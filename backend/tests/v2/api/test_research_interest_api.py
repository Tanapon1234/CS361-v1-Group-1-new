"""Master list (`/research-interests`) and per-lecturer sets."""

from collections.abc import Iterator
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.core.database import get_session
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.v2.dependencies import get_research_interest_service
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.research_interest_dto import ResearchInterestResponse
from app.v2.services.research_interest_service import ResearchInterestService

MASTER = "/api/v2/research-interests"


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(ResearchInterestService, instance=True)
    app.dependency_overrides[get_research_interest_service] = lambda: service
    return service


def interest(research_interest_id: int = 1) -> ResearchInterestResponse:
    return ResearchInterestResponse(
        research_interest_id=research_interest_id, name="Machine Learning"
    )


def test_list_research_interests(client: TestClient, service: MagicMock) -> None:
    service.list_research_interests.return_value = PageResponse[ResearchInterestResponse](
        items=[interest()], meta=PageMeta(total=1, limit=20, offset=0)
    )

    response = client.get(MASTER, params={"q": "learn"})

    assert response.status_code == 200
    assert response.json()["items"][0]["name"] == "Machine Learning"


def test_create_research_interest(client: TestClient, service: MagicMock) -> None:
    service.create_research_interest.return_value = interest()

    response = client.post(MASTER, json={"name": "Machine Learning"})

    assert response.status_code == 201
    assert response.json() == {
        "research_interest_id": 1,
        "name": "Machine Learning",
    }


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"name": ""},
        {"name": "   "},
        {"name": None},
        {"name": "x" * 256},
        {"name": "Machine Learning", "unknown": True},
    ],
    ids=["missing-name", "empty-name", "blank-name", "null-name", "too-long", "unknown-field"],
)
def test_create_research_interest_invalid_body_is_422(
    client: TestClient, service: MagicMock, body: dict[str, object]
) -> None:
    response = client.post(MASTER, json=body)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.create_research_interest.assert_not_called()


def test_create_research_interest_duplicate_name_is_409(
    client: TestClient, service: MagicMock
) -> None:
    service.create_research_interest.side_effect = ConflictError(
        "Research interest name already exists"
    )

    response = client.post(MASTER, json={"name": "Machine Learning"})

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")


def test_create_research_interest_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.create_research_interest.side_effect = ServiceUnavailableError("Database unavailable")

    response = client.post(MASTER, json={"name": "Machine Learning"})

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


def test_update_research_interest(client: TestClient, service: MagicMock) -> None:
    service.update_research_interest.return_value = interest(3)

    response = client.patch(f"{MASTER}/3", json={"name": "Deep Learning"})

    assert response.status_code == 200


def test_delete_research_interest(client: TestClient, service: MagicMock) -> None:
    response = client.delete(f"{MASTER}/3")

    assert response.status_code == 204
    service.delete_research_interest.assert_called_once_with(3)


def test_list_lecturer_research_interests(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_research_interests.return_value = ListResponse[ResearchInterestResponse](
        items=[interest()], meta=ListMeta(count=1)
    )

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/research-interests")

    assert response.status_code == 200


def test_replace_lecturer_research_interests(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.replace_lecturer_research_interests.return_value = ListResponse[
        ResearchInterestResponse
    ](items=[], meta=ListMeta(count=0))

    response = client.put(
        f"/api/v2/lecturers/{lecturer_id}/research-interests",
        json={"research_interest_ids": [1, 2]},
    )

    assert response.status_code == 200
    _, data = service.replace_lecturer_research_interests.call_args.args
    assert data.research_interest_ids == [1, 2]


def test_remove_lecturer_research_interest(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/research-interests/2")

    assert response.status_code == 204
    service.remove_lecturer_research_interest.assert_called_once_with(lecturer_id, 2)


def test_post_then_get_finds_created_research_interest(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE research_interest (
                    research_interest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE
                )
                """
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        create_response = client.post(MASTER, json={"name": "Machine Learning"})
        duplicate_response = client.post(MASTER, json={"name": "Machine Learning"})
        list_response = client.get(MASTER, params={"q": "Machine"})

    assert create_response.status_code == 201
    assert create_response.json()["research_interest_id"] == 1
    assert duplicate_response.status_code == 409
    assert list_response.status_code == 200
    assert list_response.json()["items"] == [
        {"research_interest_id": 1, "name": "Machine Learning"}
    ]


def test_create_research_interest_rolls_back_when_insert_fails(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE research_interest (
                    research_interest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER fail_research_interest_insert
                BEFORE INSERT ON research_interest
                BEGIN
                    SELECT RAISE(ABORT, 'forced insert failure');
                END
                """
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(MASTER, json={"name": "Machine Learning"})

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM research_interest")).scalar_one()

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert count == 0
