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
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.dependencies import get_research_interest_service
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.research_interest_dto import ResearchInterestResponse
from app.v2.models.lecturer import Lecturer
from app.v2.models.research_interest import FacultyResearchInterest, ResearchInterest
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


def interest_page(*items: ResearchInterestResponse) -> PageResponse[ResearchInterestResponse]:
    return PageResponse[ResearchInterestResponse](
        items=list(items),
        meta=PageMeta(total=len(items), limit=20, offset=0),
    )


def lecturer_interest_list(
    *items: ResearchInterestResponse,
) -> ListResponse[ResearchInterestResponse]:
    return ListResponse[ResearchInterestResponse](
        items=list(items), meta=ListMeta(count=len(items))
    )


def test_list_research_interests(client: TestClient, service: MagicMock) -> None:
    service.list_research_interests.return_value = interest_page(interest())

    response = client.get(MASTER, params={"q": "learn"})

    assert response.status_code == 200
    assert response.json()["items"][0]["name"] == "Machine Learning"
    assert response.json()["meta"] == {
        "total": 1,
        "limit": 20,
        "offset": 0,
    }
    query = service.list_research_interests.call_args.args[0]
    assert query.q == "learn"


def test_list_research_interests_parses_limit_and_offset(
    client: TestClient, service: MagicMock
) -> None:
    service.list_research_interests.return_value = PageResponse[ResearchInterestResponse](
        items=[], meta=PageMeta(total=0, limit=10, offset=20)
    )

    response = client.get(MASTER, params={"limit": 10, "offset": 20})

    assert response.status_code == 200
    query = service.list_research_interests.call_args.args[0]
    assert query.limit == 10
    assert query.offset == 20


@pytest.mark.parametrize(
    "params",
    [{"limit": "101"}, {"limit": "hello"}, {"offset": "-1"}],
    ids=["limit-too-large", "limit-not-integer", "offset-negative"],
)
def test_list_research_interests_invalid_query_is_422(
    client: TestClient, service: MagicMock, params: dict[str, str]
) -> None:
    response = client.get(MASTER, params=params)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.list_research_interests.assert_not_called()


def test_list_research_interests_service_error_is_problem_response(
    client: TestClient, service: MagicMock
) -> None:
    service.list_research_interests.side_effect = ServiceUnavailableError("Database unavailable")

    response = client.get(MASTER)

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


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
    service.update_research_interest.return_value = ResearchInterestResponse(
        research_interest_id=3, name="Deep Learning"
    )

    response = client.patch(f"{MASTER}/3", json={"name": "Deep Learning"})

    assert response.status_code == 200
    assert response.json() == {"research_interest_id": 3, "name": "Deep Learning"}
    research_interest_id, data = service.update_research_interest.call_args.args
    assert research_interest_id == 3
    assert data.name == "Deep Learning"


def test_update_unknown_research_interest_is_404(client: TestClient, service: MagicMock) -> None:
    service.update_research_interest.side_effect = NotFoundError("Research interest not found")

    response = client.patch(f"{MASTER}/99", json={"name": "Deep Learning"})

    assert response.status_code == 404


@pytest.mark.parametrize(
    "research_interest_id",
    ["abc", "32768"],
    ids=["not-numeric", "exceeds-smallint"],
)
def test_update_research_interest_invalid_id_is_422(
    client: TestClient, service: MagicMock, research_interest_id: str
) -> None:
    response = client.patch(f"{MASTER}/{research_interest_id}", json={"name": "Deep Learning"})

    assert response.status_code == 422
    service.update_research_interest.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [{}, {"name": ""}, {"name": None}, {"name": "Deep Learning", "unknown": True}],
    ids=["missing-name", "empty-name", "null-name", "unknown-field"],
)
def test_update_research_interest_invalid_body_is_422(
    client: TestClient, service: MagicMock, body: dict[str, object]
) -> None:
    response = client.patch(f"{MASTER}/1", json=body)

    assert response.status_code == 422
    service.update_research_interest.assert_not_called()


def test_update_research_interest_duplicate_name_is_409(
    client: TestClient, service: MagicMock
) -> None:
    service.update_research_interest.side_effect = ConflictError(
        "Research interest name already exists"
    )

    response = client.patch(f"{MASTER}/1", json={"name": "Deep Learning"})

    assert response.status_code == 409


def test_update_research_interest_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.update_research_interest.side_effect = ServiceUnavailableError("Database unavailable")

    response = client.patch(f"{MASTER}/1", json={"name": "Deep Learning"})

    assert response.status_code == 503


def test_delete_research_interest(client: TestClient, service: MagicMock) -> None:
    response = client.delete(f"{MASTER}/3")

    assert response.status_code == 204
    assert response.content == b""
    service.delete_research_interest.assert_called_once_with(3)


def test_delete_unknown_research_interest_is_404(client: TestClient, service: MagicMock) -> None:
    service.delete_research_interest.side_effect = NotFoundError("Research interest not found")

    response = client.delete(f"{MASTER}/99")

    assert response.status_code == 404
    service.delete_research_interest.assert_called_once_with(99)


def test_list_lecturer_research_interests(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_research_interests.return_value = lecturer_interest_list(interest())

    response = client.get(
        f"/api/v2/lecturers/{lecturer_id}/research-interests",
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"research_interest_id": 1, "name": "Machine Learning"}],
        "meta": {"count": 1},
    }
    service.list_lecturer_research_interests.assert_called_once_with(lecturer_id)


def test_list_lecturer_research_interests_empty(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_research_interests.return_value = lecturer_interest_list()

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/research-interests")

    assert response.status_code == 200
    assert response.json() == {"items": [], "meta": {"count": 0}}


def test_list_lecturer_research_interests_invalid_uuid_is_422(
    client: TestClient, service: MagicMock
) -> None:
    response = client.get("/api/v2/lecturers/not-a-uuid/research-interests")

    assert response.status_code == 422
    service.list_lecturer_research_interests.assert_not_called()


def test_list_unknown_lecturer_research_interests_is_404(
    client: TestClient, service: MagicMock
) -> None:
    service.list_lecturer_research_interests.side_effect = NotFoundError("Lecturer not found")

    response = client.get(f"/api/v2/lecturers/{uuid4()}/research-interests")

    assert response.status_code == 404


def test_replace_lecturer_research_interests(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.replace_lecturer_research_interests.return_value = ListResponse[
        ResearchInterestResponse
    ](
        items=[
            ResearchInterestResponse(research_interest_id=1, name="Machine Learning"),
            ResearchInterestResponse(research_interest_id=3, name="Computer Vision"),
        ],
        meta=ListMeta(count=2),
    )

    response = client.put(
        f"/api/v2/lecturers/{lecturer_id}/research-interests",
        json={"research_interest_ids": [1, 3]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"research_interest_id": 1, "name": "Machine Learning"},
            {"research_interest_id": 3, "name": "Computer Vision"},
        ],
        "meta": {"count": 2},
    }
    _, data = service.replace_lecturer_research_interests.call_args.args
    assert data.research_interest_ids == [1, 3]


@pytest.mark.parametrize(
    ("lecturer_id", "body"),
    [
        ("not-a-uuid", {"research_interest_ids": [1]}),
        (str(uuid4()), {}),
        (str(uuid4()), {"research_interest_ids": [0]}),
        (str(uuid4()), {"research_interest_ids": [32768]}),
        (str(uuid4()), {"research_interest_ids": ["1"]}),
        (str(uuid4()), {"research_interest_ids": [1, 1]}),
    ],
    ids=[
        "invalid-uuid",
        "missing-ids",
        "id-too-small",
        "id-exceeds-smallint",
        "id-not-integer",
        "duplicate-id",
    ],
)
def test_replace_lecturer_research_interests_invalid_request_is_422(
    client: TestClient, service: MagicMock, lecturer_id: str, body: object
) -> None:
    response = client.put(
        f"/api/v2/lecturers/{lecturer_id}/research-interests",
        json=body,
    )

    assert response.status_code == 422
    service.replace_lecturer_research_interests.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [NotFoundError("Lecturer not found"), NotFoundError("Research interest 99 not found")],
    ids=["unknown-lecturer", "unknown-interest"],
)
def test_replace_lecturer_research_interests_not_found_is_404(
    client: TestClient, service: MagicMock, error: NotFoundError
) -> None:
    service.replace_lecturer_research_interests.side_effect = error

    response = client.put(
        f"/api/v2/lecturers/{uuid4()}/research-interests",
        json={"research_interest_ids": [1, 99]},
    )

    assert response.status_code == 404


def test_replace_lecturer_research_interests_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.replace_lecturer_research_interests.side_effect = ServiceUnavailableError(
        "Database unavailable"
    )

    response = client.put(
        f"/api/v2/lecturers/{uuid4()}/research-interests",
        json={"research_interest_ids": [1]},
    )

    assert response.status_code == 503


def test_remove_lecturer_research_interest(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/research-interests/2")

    assert response.status_code == 204
    assert response.content == b""
    service.remove_lecturer_research_interest.assert_called_once_with(lecturer_id, 2)


@pytest.mark.parametrize(
    "error",
    [
        NotFoundError("Lecturer not found"),
        NotFoundError("Research interest relationship not found"),
    ],
    ids=["unknown-lecturer", "unknown-relationship"],
)
def test_remove_lecturer_research_interest_not_found_is_404(
    client: TestClient, service: MagicMock, error: NotFoundError
) -> None:
    lecturer_id = uuid4()
    service.remove_lecturer_research_interest.side_effect = error

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/research-interests/2")

    assert response.status_code == 404
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
    assert list_response.json()["meta"] == {
        "total": 1,
        "limit": 20,
        "offset": 0,
    }


def test_list_research_interests_search_and_pagination(app: FastAPI) -> None:
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
                INSERT INTO research_interest (name)
                VALUES
                    ('Artificial Intelligence'),
                    ('Machine Learning'),
                    ('Machine Learning in Healthcare'),
                    ('Robotics')
                """
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        search_response = client.get(MASTER, params={"q": "machine"})
        paged_response = client.get(MASTER, params={"limit": 2, "offset": 1})
        empty_response = client.get(MASTER, params={"q": "quantum"})

    assert search_response.status_code == 200
    assert [item["name"] for item in search_response.json()["items"]] == [
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]
    assert search_response.json()["meta"]["total"] == 2

    assert [item["name"] for item in paged_response.json()["items"]] == [
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]
    assert paged_response.json()["meta"] == {
        "total": 4,
        "limit": 2,
        "offset": 1,
    }

    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }


def test_put_lecturer_research_interests_replaces_and_clears_relationships(
    app: FastAPI,
) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    ResearchInterest.__table__.create(engine)
    FacultyResearchInterest.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="Somchai",
                    email="somchai@example.ac.th",
                ),
                ResearchInterest(research_interest_id=1, name="Machine Learning"),
                ResearchInterest(research_interest_id=2, name="Data Mining"),
                ResearchInterest(research_interest_id=3, name="Computer Vision"),
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=1),
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=2),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override
    url = f"/api/v2/lecturers/{lecturer_id}/research-interests"

    with TestClient(app) as client:
        replace_response = client.put(url, json={"research_interest_ids": [1, 3]})
        replaced_get_response = client.get(url)
        clear_response = client.put(url, json={"research_interest_ids": []})
        cleared_get_response = client.get(url)

    assert replace_response.status_code == 200
    assert replace_response.json() == {
        "items": [
            {"research_interest_id": 1, "name": "Machine Learning"},
            {"research_interest_id": 3, "name": "Computer Vision"},
        ],
        "meta": {"count": 2},
    }
    assert replaced_get_response.status_code == 200
    assert [item["research_interest_id"] for item in replaced_get_response.json()["items"]] == [
        3,
        1,
    ]
    assert clear_response.status_code == 200
    assert clear_response.json() == {"items": [], "meta": {"count": 0}}
    assert cleared_get_response.status_code == 200
    assert cleared_get_response.json() == {"items": [], "meta": {"count": 0}}


def test_delete_research_interest_removes_record_and_cascades_relationship(
    app: FastAPI,
) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
    Lecturer.__table__.create(engine)
    ResearchInterest.__table__.create(engine)
    FacultyResearchInterest.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="Somchai",
                    email="somchai@example.ac.th",
                ),
                ResearchInterest(research_interest_id=1, name="Machine Learning"),
                ResearchInterest(research_interest_id=2, name="Computer Vision"),
            ]
        )
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=1),
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=2),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override
    lecturer_url = f"/api/v2/lecturers/{lecturer_id}/research-interests"

    with TestClient(app) as client:
        delete_response = client.delete(f"{MASTER}/1")
        master_response = client.get(MASTER)
        lecturer_response = client.get(lecturer_url)

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert master_response.json()["items"] == [
        {"research_interest_id": 2, "name": "Computer Vision"}
    ]
    assert lecturer_response.json() == {
        "items": [{"research_interest_id": 2, "name": "Computer Vision"}],
        "meta": {"count": 1},
    }


def test_remove_lecturer_research_interest_only_removes_requested_relationship(
    app: FastAPI,
) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
    Lecturer.__table__.create(engine)
    ResearchInterest.__table__.create(engine)
    FacultyResearchInterest.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="Somchai",
                    email="somchai@example.ac.th",
                ),
                Lecturer(
                    lecturer_id=other_lecturer_id,
                    name_th="Somsri",
                    email="somsri@example.ac.th",
                ),
                ResearchInterest(research_interest_id=1, name="Machine Learning"),
                ResearchInterest(research_interest_id=2, name="Computer Vision"),
            ]
        )
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=1),
                FacultyResearchInterest(lecturer_id=lecturer_id, research_interest_id=2),
                FacultyResearchInterest(lecturer_id=other_lecturer_id, research_interest_id=1),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override
    relationship_url = f"/api/v2/lecturers/{lecturer_id}/research-interests/1"
    lecturer_url = f"/api/v2/lecturers/{lecturer_id}/research-interests"
    other_lecturer_url = f"/api/v2/lecturers/{other_lecturer_id}/research-interests"

    with TestClient(app) as client:
        delete_response = client.delete(relationship_url)
        lecturer_response = client.get(lecturer_url)
        other_lecturer_response = client.get(other_lecturer_url)
        master_response = client.get(MASTER)
        repeated_delete_response = client.delete(relationship_url)
        unknown_lecturer_response = client.delete(
            f"/api/v2/lecturers/{uuid4()}/research-interests/1"
        )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert lecturer_response.json() == {
        "items": [{"research_interest_id": 2, "name": "Computer Vision"}],
        "meta": {"count": 1},
    }
    assert other_lecturer_response.json() == {
        "items": [{"research_interest_id": 1, "name": "Machine Learning"}],
        "meta": {"count": 1},
    }
    assert [item["research_interest_id"] for item in master_response.json()["items"]] == [
        2,
        1,
    ]
    assert repeated_delete_response.status_code == 404
    assert unknown_lecturer_response.status_code == 404
