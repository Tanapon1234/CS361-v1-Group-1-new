"""Master list (`/research-interests`) and per-lecturer sets."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
