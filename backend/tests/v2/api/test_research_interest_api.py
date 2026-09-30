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
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.v2.dependencies import get_research_interest_service
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestListResponse,
    ResearchInterestListResponse,
    ResearchInterestPagination,
    ResearchInterestResponse,
)
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


def interest_list(*items: ResearchInterestResponse) -> ResearchInterestListResponse:
    return ResearchInterestListResponse(
        data=list(items),
        pagination=ResearchInterestPagination(
            page=1, limit=20, total=len(items), total_pages=1 if items else 0
        ),
    )


def lecturer_interest_list(
    *items: ResearchInterestResponse,
) -> LecturerResearchInterestListResponse:
    return LecturerResearchInterestListResponse(data=list(items))


def test_list_research_interests(client: TestClient, service: MagicMock) -> None:
    service.list_research_interests.return_value = interest_list(interest())

    response = client.get(MASTER, params={"search": "learn"})

    assert response.status_code == 200
    assert response.json()["data"][0]["name"] == "Machine Learning"
    assert response.json()["pagination"] == {
        "page": 1,
        "limit": 20,
        "total": 1,
        "total_pages": 1,
    }


@pytest.mark.parametrize(
    "params",
    [{"page": "0"}, {"limit": "0"}, {"sort_order": "hello"}],
    ids=["page-too-small", "limit-too-small", "invalid-sort-order"],
)
def test_list_research_interests_invalid_query_is_400(
    client: TestClient, service: MagicMock, params: dict[str, str]
) -> None:
    response = client.get(MASTER, params=params)

    assert response.status_code == 400
    service.list_research_interests.assert_not_called()


def test_create_research_interest(client: TestClient, service: MagicMock) -> None:
    service.create_research_interest.return_value = interest()

    response = client.post(MASTER, json={"name": "Machine Learning"})

    assert response.status_code == 201
    assert response.json()["research_interest_id"] == 1


@pytest.mark.parametrize(
    "body",
    [{}, {"name": ""}],
    ids=["missing-name", "empty-name"],
)
def test_create_research_interest_invalid_body_is_400(
    client: TestClient, service: MagicMock, body: dict[str, str]
) -> None:
    response = client.post(MASTER, json=body)

    assert response.status_code == 400
    service.create_research_interest.assert_not_called()


def test_create_research_interest_duplicate_name_is_409(
    client: TestClient, service: MagicMock
) -> None:
    service.create_research_interest.side_effect = ConflictError(
        "Research interest name already exists"
    )

    response = client.post(MASTER, json={"name": "Machine Learning"})

    assert response.status_code == 409


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
    service.delete_research_interest.assert_called_once_with(3)


def test_list_lecturer_research_interests(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_research_interests.return_value = lecturer_interest_list(interest())

    response = client.get(
        f"/api/v2/lecturers/{lecturer_id}/research-interests",
        params={"search": "machine", "sort_order": "asc"},
    )

    assert response.status_code == 200
    assert response.json() == {"data": [{"research_interest_id": 1, "name": "Machine Learning"}]}


@pytest.mark.parametrize(
    "url",
    [
        "/api/v2/lecturers/not-a-uuid/research-interests",
        f"/api/v2/lecturers/{uuid4()}/research-interests?sort_order=hello",
    ],
    ids=["invalid-uuid", "invalid-sort-order"],
)
def test_list_lecturer_research_interests_invalid_params_are_400(
    client: TestClient, service: MagicMock, url: str
) -> None:
    response = client.get(url)

    assert response.status_code == 400
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
        update_response = client.patch(f"{MASTER}/1", json={"name": "Deep Learning"})
        list_response = client.get(MASTER, params={"search": "Machine"})
        updated_list_response = client.get(MASTER, params={"search": "Deep"})

    assert create_response.status_code == 201
    assert create_response.json()["research_interest_id"] == 1
    assert duplicate_response.status_code == 409
    assert update_response.status_code == 200
    assert update_response.json() == {"research_interest_id": 1, "name": "Deep Learning"}
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []
    assert list_response.json()["pagination"] == {
        "page": 1,
        "limit": 20,
        "total": 0,
        "total_pages": 0,
    }
    assert updated_list_response.status_code == 200
    assert updated_list_response.json()["data"] == [
        {"research_interest_id": 1, "name": "Deep Learning"}
    ]


def test_list_research_interests_search_pagination_and_sort(app: FastAPI) -> None:
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
        search_response = client.get(MASTER, params={"search": "machine"})
        paged_response = client.get(MASTER, params={"page": 1, "limit": 2})
        asc_response = client.get(MASTER, params={"sort_order": "asc"})
        desc_response = client.get(MASTER, params={"sort_order": "desc"})
        empty_response = client.get(MASTER, params={"search": "quantum"})

    assert search_response.status_code == 200
    assert [item["name"] for item in search_response.json()["data"]] == [
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]
    assert search_response.json()["pagination"]["total"] == 2

    assert paged_response.status_code == 200
    assert len(paged_response.json()["data"]) <= 2
    assert paged_response.json()["pagination"] == {
        "page": 1,
        "limit": 2,
        "total": 4,
        "total_pages": 2,
    }

    assert asc_response.status_code == 200
    assert [item["name"] for item in asc_response.json()["data"]] == [
        "Artificial Intelligence",
        "Machine Learning",
        "Machine Learning in Healthcare",
        "Robotics",
    ]

    assert desc_response.status_code == 200
    assert [item["name"] for item in desc_response.json()["data"]] == [
        "Robotics",
        "Machine Learning in Healthcare",
        "Machine Learning",
        "Artificial Intelligence",
    ]

    assert empty_response.status_code == 200
    assert empty_response.json() == {
        "data": [],
        "pagination": {"page": 1, "limit": 20, "total": 0, "total_pages": 0},
    }


def test_list_lecturer_research_interests_search_sort_and_scope(app: FastAPI) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
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
                Lecturer(
                    lecturer_id=other_lecturer_id,
                    name_th="Somsri",
                    email="somsri@example.ac.th",
                ),
                ResearchInterest(
                    research_interest_id=1,
                    name="Machine Learning",
                ),
                ResearchInterest(
                    research_interest_id=2,
                    name="Machine Learning in Healthcare",
                ),
                ResearchInterest(
                    research_interest_id=3,
                    name="Artificial Intelligence",
                ),
                ResearchInterest(
                    research_interest_id=4,
                    name="Machine Learning for Other Lecturer",
                ),
                FacultyResearchInterest(
                    lecturer_id=lecturer_id,
                    research_interest_id=1,
                ),
                FacultyResearchInterest(
                    lecturer_id=lecturer_id,
                    research_interest_id=2,
                ),
                FacultyResearchInterest(
                    lecturer_id=lecturer_id,
                    research_interest_id=3,
                ),
                FacultyResearchInterest(
                    lecturer_id=other_lecturer_id,
                    research_interest_id=4,
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        all_response = client.get(f"/api/v2/lecturers/{lecturer_id}/research-interests")
        search_response = client.get(
            f"/api/v2/lecturers/{lecturer_id}/research-interests",
            params={"search": "machine"},
        )
        desc_response = client.get(
            f"/api/v2/lecturers/{lecturer_id}/research-interests",
            params={"sort_order": "desc"},
        )
        empty_response = client.get(
            f"/api/v2/lecturers/{lecturer_id}/research-interests",
            params={"search": "quantum"},
        )
        unknown_response = client.get(f"/api/v2/lecturers/{uuid4()}/research-interests")

    assert all_response.status_code == 200
    assert [item["name"] for item in all_response.json()["data"]] == [
        "Artificial Intelligence",
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]

    assert search_response.status_code == 200
    assert [item["name"] for item in search_response.json()["data"]] == [
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]

    assert desc_response.status_code == 200
    assert [item["name"] for item in desc_response.json()["data"]] == [
        "Machine Learning in Healthcare",
        "Machine Learning",
        "Artificial Intelligence",
    ]

    assert empty_response.status_code == 200
    assert empty_response.json() == {"data": []}
    assert unknown_response.status_code == 404


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

    with engine.connect() as connection:
        replaced_ids = (
            connection.execute(
                text(
                    "SELECT research_interest_id FROM faculty_research_interest "
                    "WHERE lecturer_id = :lecturer_id ORDER BY research_interest_id"
                ),
                {"lecturer_id": lecturer_id.hex},
            )
            .scalars()
            .all()
        )

    with TestClient(app) as client:
        clear_response = client.put(url, json={"research_interest_ids": []})

    with engine.connect() as connection:
        cleared_ids = (
            connection.execute(
                text(
                    "SELECT research_interest_id FROM faculty_research_interest "
                    "WHERE lecturer_id = :lecturer_id"
                ),
                {"lecturer_id": lecturer_id.hex},
            )
            .scalars()
            .all()
        )

    assert replace_response.status_code == 200
    assert replace_response.json() == {
        "items": [
            {"research_interest_id": 1, "name": "Machine Learning"},
            {"research_interest_id": 3, "name": "Computer Vision"},
        ],
        "meta": {"count": 2},
    }
    assert replaced_ids == [1, 3]
    assert clear_response.status_code == 200
    assert clear_response.json() == {"items": [], "meta": {"count": 0}}
    assert cleared_ids == []


def test_put_lecturer_research_interests_rolls_back_when_replace_fails(
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
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TRIGGER fail_research_interest_3
                BEFORE INSERT ON faculty_research_interest
                WHEN NEW.research_interest_id = 3
                BEGIN
                    SELECT RAISE(ABORT, 'forced replace failure');
                END
                """
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_research_interest_service, None)
    app.dependency_overrides[get_session] = session_override
    url = f"/api/v2/lecturers/{lecturer_id}/research-interests"

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.put(url, json={"research_interest_ids": [1, 3]})

    with engine.connect() as connection:
        remaining_ids = (
            connection.execute(
                text(
                    "SELECT research_interest_id FROM faculty_research_interest "
                    "WHERE lecturer_id = :lecturer_id ORDER BY research_interest_id"
                ),
                {"lecturer_id": lecturer_id.hex},
            )
            .scalars()
            .all()
        )

    assert response.status_code == 500
    assert remaining_ids == [1, 2]
