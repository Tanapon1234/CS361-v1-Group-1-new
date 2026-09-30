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
