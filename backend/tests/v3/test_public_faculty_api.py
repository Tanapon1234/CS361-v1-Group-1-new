"""`/public/v3` answers without any sign-in, and the signed-in API still refuses anonymous calls."""

from collections.abc import Iterator
from unittest.mock import create_autospec
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.v3.dependencies import get_public_faculty_service
from app.v3.dtos.public_faculty_dto import PublicFacultyList
from app.v3.services.public_faculty_service import PublicFacultyService


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    service = create_autospec(PublicFacultyService, instance=True)
    service.list_faculties.return_value = PublicFacultyList(data=[])
    app.dependency_overrides[get_public_faculty_service] = lambda: service
    with TestClient(app) as client:
        yield client


def test_list_needs_no_sign_in(client: TestClient) -> None:
    response = client.get("/public/v3/faculties")

    assert response.status_code == 200
    assert response.json() == {"data": []}


def test_public_api_is_read_only(client: TestClient) -> None:
    assert client.post("/public/v3/faculties", json={}).status_code == 405
    assert client.delete(f"/public/v3/faculties/{uuid4()}").status_code == 405


def test_signed_in_api_still_needs_sign_in(client: TestClient) -> None:
    assert client.get("/api/v3/lecturers").status_code == 401
