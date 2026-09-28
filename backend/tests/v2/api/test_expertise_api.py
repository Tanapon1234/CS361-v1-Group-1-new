"""Master list (`/expertise`) and per-lecturer sets."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.v2.dependencies import get_expertise_service
from app.v2.dtos.common import ListMeta, ListResponse, PageMeta, PageResponse
from app.v2.dtos.expertise_dto import ExpertiseResponse
from app.v2.services.expertise_service import ExpertiseService

MASTER = "/api/v2/expertise"


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(ExpertiseService, instance=True)
    app.dependency_overrides[get_expertise_service] = lambda: service
    return service


def expertise(expertise_id: int = 1) -> ExpertiseResponse:
    return ExpertiseResponse(expertise_id=expertise_id, description="Cloud Computing")


def test_list_expertise(client: TestClient, service: MagicMock) -> None:
    service.list_expertise.return_value = PageResponse[ExpertiseResponse](
        items=[expertise()], meta=PageMeta(total=1, limit=20, offset=0)
    )

    response = client.get(MASTER)

    assert response.status_code == 200


def test_create_expertise(client: TestClient, service: MagicMock) -> None:
    service.create_expertise.return_value = expertise()

    response = client.post(MASTER, json={"description": "Cloud Computing"})

    assert response.status_code == 201


def test_get_expertise(client: TestClient, service: MagicMock) -> None:
    service.get_expertise.return_value = expertise(5)

    response = client.get(f"{MASTER}/5")

    assert response.status_code == 200
    service.get_expertise.assert_called_once_with(5)


def test_get_unknown_expertise_is_404(client: TestClient, service: MagicMock) -> None:
    service.get_expertise.side_effect = NotFoundError("Expertise not found")

    response = client.get(f"{MASTER}/5")

    assert response.status_code == 404


def test_update_expertise(client: TestClient, service: MagicMock) -> None:
    service.update_expertise.return_value = expertise(5)

    response = client.patch(f"{MASTER}/5", json={"description": "Distributed Systems"})

    assert response.status_code == 200


def test_delete_expertise(client: TestClient, service: MagicMock) -> None:
    response = client.delete(f"{MASTER}/5")

    assert response.status_code == 204


def test_list_lecturer_expertise(client: TestClient, service: MagicMock) -> None:
    service.list_lecturer_expertise.return_value = ListResponse[ExpertiseResponse](
        items=[expertise()], meta=ListMeta(count=1)
    )

    response = client.get(f"/api/v2/lecturers/{uuid4()}/expertise")

    assert response.status_code == 200


def test_replace_lecturer_expertise(client: TestClient, service: MagicMock) -> None:
    service.replace_lecturer_expertise.return_value = ListResponse[ExpertiseResponse](
        items=[], meta=ListMeta(count=0)
    )

    response = client.put(f"/api/v2/lecturers/{uuid4()}/expertise", json={"expertise_ids": [1]})

    assert response.status_code == 200


def test_remove_lecturer_expertise(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/expertise/1")

    assert response.status_code == 204
    service.remove_lecturer_expertise.assert_called_once_with(lecturer_id, 1)
