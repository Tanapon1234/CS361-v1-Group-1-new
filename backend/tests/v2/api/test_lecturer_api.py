"""Lecturer API contract tests and focused database integration tests.

The service is a strict mock (`create_autospec`), so these pass before the service exists
and keep guarding the HTTP contract after it is implemented. Use this file as the example
when adding tests.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.core.database import get_session
from app.core.exceptions import ConflictError, NotFoundError
from app.v2.dependencies import get_lecturer_service
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.lecturer_dto import LecturerListQuery, LecturerResponse
from app.v2.models.lecturer import Lecturer
from app.v2.services.lecturer_service import LecturerService

BASE = "/api/v2/lecturers"


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(LecturerService, instance=True)
    app.dependency_overrides[get_lecturer_service] = lambda: service
    return service


def make_lecturer(**overrides: Any) -> LecturerResponse:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "lecturer_id": uuid4(),
        "name_th": "ผศ.ดร.สมชาย ใจดี",
        "name_en": "Asst. Prof. Somchai Jaidee",
        "rank": "Assistant Professor",
        "profile_image_url": None,
        "office": None,
        "phone": None,
        "phone_extension": None,
        "email": "somchai@example.ac.th",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    return LecturerResponse(**(values | overrides))


def test_create_lecturer(client: TestClient, service: MagicMock) -> None:
    lecturer = make_lecturer()
    service.create_lecturer.return_value = lecturer

    response = client.post(BASE, json={"name_th": "สมชาย", "email": "somchai@example.ac.th"})

    assert response.status_code == 201
    assert response.json()["lecturer_id"] == str(lecturer.lecturer_id)


@pytest.mark.parametrize(
    "body",
    [
        {"email": "somchai@example.ac.th"},
        {"name_th": "สมชาย"},
        {"name_th": "สมชาย", "email": "not-an-email"},
        {"name_th": "สมชาย", "email": "somchai@example.ac.th", "salary": 1},
    ],
    ids=["missing-name_th", "missing-email", "bad-email", "unknown-field"],
)
def test_create_lecturer_validates_body(
    client: TestClient, service: MagicMock, body: dict[str, Any]
) -> None:
    response = client.post(BASE, json=body)

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    service.create_lecturer.assert_not_called()


def test_create_lecturer_conflict_is_409(client: TestClient, service: MagicMock) -> None:
    service.create_lecturer.side_effect = ConflictError("Email already used")

    response = client.post(BASE, json={"name_th": "สมชาย", "email": "dup@example.ac.th"})

    assert response.status_code == 409


def test_post_lecturer_persists_and_rejects_duplicate_email(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    payload = {
        "name_th": "ผศ.ดร.สมชาย ใจดี",
        "name_en": "Asst. Prof. Somchai Jaidee",
        "email": "somchai@example.ac.th",
    }
    with TestClient(app) as client:
        create_response = client.post(BASE, json=payload)
        duplicate_response = client.post(BASE, json=payload)

    assert create_response.status_code == 201
    assert create_response.json()["name_th"] == payload["name_th"]
    assert create_response.json()["is_active"] is True
    assert duplicate_response.status_code == 409

    with Session(engine) as session:
        lecturers = session.exec(select(Lecturer)).all()
    assert len(lecturers) == 1
    assert lecturers[0].email == payload["email"]


def test_post_activate_lecturer_persists_status(app: FastAPI) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add(
            Lecturer(
                lecturer_id=lecturer_id,
                name_th="สมชาย",
                email="somchai@example.ac.th",
                is_active=False,
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        response = client.post(f"{BASE}/{lecturer_id}/activate")

    assert response.status_code == 200
    assert response.json()["is_active"] is True
    with Session(engine) as session:
        lecturer = session.get(Lecturer, lecturer_id)
    assert lecturer is not None
    assert lecturer.is_active is True


def test_post_deactivate_lecturer_persists_status(app: FastAPI) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add(
            Lecturer(
                lecturer_id=lecturer_id,
                name_th="สมชาย",
                email="somchai@example.ac.th",
                is_active=True,
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        response = client.post(f"{BASE}/{lecturer_id}/deactivate")

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    with Session(engine) as session:
        lecturer = session.get(Lecturer, lecturer_id)
    assert lecturer is not None
    assert lecturer.is_active is False


def test_list_lecturers_passes_query(client: TestClient, service: MagicMock) -> None:
    service.list_lecturers.return_value = PageResponse[LecturerResponse](
        items=[make_lecturer()], meta=PageMeta(total=1, limit=5, offset=0)
    )

    response = client.get(BASE, params={"q": "somchai", "is_active": "true", "limit": 5})

    assert response.status_code == 200
    assert response.json()["meta"] == {"total": 1, "limit": 5, "offset": 0}
    service.list_lecturers.assert_called_once_with(
        LecturerListQuery(q="somchai", is_active=True, limit=5)
    )


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}],
    ids=["zero-limit", "limit-too-large", "negative-offset"],
)
def test_list_lecturers_validates_pagination(
    client: TestClient, service: MagicMock, params: dict[str, int]
) -> None:
    response = client.get(BASE, params=params)

    assert response.status_code == 422
    service.list_lecturers.assert_not_called()


def test_list_lecturers_searches_filters_and_paginates(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    name_th="Alpha",
                    name_en="Alice Smith",
                    email="alpha@example.ac.th",
                    is_active=True,
                ),
                Lecturer(
                    name_th="Beta",
                    name_en="Bob Jones",
                    email="search-email@example.ac.th",
                    is_active=False,
                ),
                Lecturer(
                    name_th="Gamma",
                    email="gamma@example.ac.th",
                    is_active=True,
                ),
                Lecturer(
                    name_th="สมชาย",
                    name_en="Somchai Jaidee",
                    email="somchai@example.ac.th",
                    is_active=True,
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        page_response = client.get(BASE, params={"limit": 2, "offset": 1})
        english_name_response = client.get(BASE, params={"q": "ALICE"})
        email_response = client.get(BASE, params={"q": "SEARCH-EMAIL"})
        thai_name_response = client.get(BASE, params={"q": "สม"})
        inactive_response = client.get(BASE, params={"is_active": "false"})
        empty_response = client.get(BASE, params={"q": "does-not-exist"})

    assert page_response.status_code == 200
    assert [item["name_th"] for item in page_response.json()["items"]] == ["Beta", "Gamma"]
    assert page_response.json()["meta"] == {"total": 4, "limit": 2, "offset": 1}

    assert [item["name_th"] for item in english_name_response.json()["items"]] == ["Alpha"]
    assert [item["name_th"] for item in email_response.json()["items"]] == ["Beta"]
    assert [item["name_th"] for item in thai_name_response.json()["items"]] == ["สมชาย"]
    assert [item["name_th"] for item in inactive_response.json()["items"]] == ["Beta"]
    assert empty_response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }


def test_get_lecturer_reads_database_and_returns_not_found(app: FastAPI) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add(
            Lecturer(
                lecturer_id=lecturer_id,
                name_th="สมชาย",
                name_en="Somchai Jaidee",
                email="somchai@example.ac.th",
                is_active=False,
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        found_response = client.get(f"{BASE}/{lecturer_id}")
        missing_response = client.get(f"{BASE}/{uuid4()}")

    assert found_response.status_code == 200
    assert found_response.json()["lecturer_id"] == str(lecturer_id)
    assert found_response.json()["name_en"] == "Somchai Jaidee"
    assert found_response.json()["is_active"] is False
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Lecturer not found"


def test_get_lecturer(client: TestClient, service: MagicMock) -> None:
    lecturer = make_lecturer()
    service.get_lecturer.return_value = lecturer

    response = client.get(f"{BASE}/{lecturer.lecturer_id}")

    assert response.status_code == 200
    service.get_lecturer.assert_called_once_with(lecturer.lecturer_id)


def test_get_unknown_lecturer_is_404(client: TestClient, service: MagicMock) -> None:
    service.get_lecturer.side_effect = NotFoundError("Lecturer not found")

    response = client.get(f"{BASE}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Lecturer not found"


def test_lecturer_id_must_be_a_uuid(client: TestClient, service: MagicMock) -> None:
    response = client.get(f"{BASE}/123")

    assert response.status_code == 422
    service.get_lecturer.assert_not_called()


def test_update_lecturer_sends_only_given_fields(client: TestClient, service: MagicMock) -> None:
    lecturer = make_lecturer()
    service.update_lecturer.return_value = lecturer

    response = client.patch(f"{BASE}/{lecturer.lecturer_id}", json={"office": "SC-201"})

    assert response.status_code == 200
    _, data = service.update_lecturer.call_args.args
    assert data.model_dump(exclude_unset=True) == {"office": "SC-201"}


@pytest.mark.parametrize(
    "body",
    [
        {"name_th": None},
        {"email": None},
        {"email": "not-an-email"},
        {"name_th": ""},
        {"salary": 1},
        {"is_active": False},
    ],
    ids=[
        "null-name-th",
        "null-email",
        "bad-email",
        "empty-name-th",
        "unknown-field",
        "status-not-patchable",
    ],
)
def test_update_lecturer_validates_body(
    client: TestClient, service: MagicMock, body: dict[str, Any]
) -> None:
    response = client.patch(f"{BASE}/{uuid4()}", json=body)

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    service.update_lecturer.assert_not_called()


def test_patch_lecturer_persists_partial_update_and_handles_errors(app: FastAPI) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="สมชาย",
                    name_en="Somchai Jaidee",
                    office="SC-101",
                    email="somchai@example.ac.th",
                ),
                Lecturer(
                    lecturer_id=other_lecturer_id,
                    name_th="สมหญิง",
                    email="somying@example.ac.th",
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_lecturer_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        update_response = client.patch(
            f"{BASE}/{lecturer_id}",
            json={"name_en": None, "office": "SC-201"},
        )
        duplicate_response = client.patch(
            f"{BASE}/{lecturer_id}",
            json={"email": "somying@example.ac.th"},
        )
        missing_response = client.patch(
            f"{BASE}/{uuid4()}",
            json={"office": "SC-301"},
        )

    assert update_response.status_code == 200
    assert update_response.json()["name_th"] == "สมชาย"
    assert update_response.json()["name_en"] is None
    assert update_response.json()["office"] == "SC-201"
    assert update_response.json()["email"] == "somchai@example.ac.th"
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Email already used"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Lecturer not found"

    with Session(engine) as session:
        lecturer = session.get(Lecturer, lecturer_id)
    assert lecturer is not None
    assert lecturer.name_en is None
    assert lecturer.office == "SC-201"
    assert lecturer.email == "somchai@example.ac.th"


@pytest.mark.parametrize(
    ("action", "method", "is_active"),
    [("activate", "activate_lecturer", True), ("deactivate", "deactivate_lecturer", False)],
)
def test_activate_and_deactivate(
    client: TestClient, service: MagicMock, action: str, method: str, is_active: bool
) -> None:
    lecturer = make_lecturer(is_active=is_active)
    getattr(service, method).return_value = lecturer

    response = client.post(f"{BASE}/{lecturer.lecturer_id}/{action}")

    assert response.status_code == 200
    assert response.json()["is_active"] is is_active
