from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.v2.dependencies import get_publication_service
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import PublicationListQuery, PublicationResponse
from app.v2.services.publication_service import PublicationService

BASE = "/api/v2/publications"


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(PublicationService, instance=True)
    app.dependency_overrides[get_publication_service] = lambda: service
    return service


def make_publication(**overrides: Any) -> PublicationResponse:
    values: dict[str, Any] = {
        "publication_id": 1,
        "title": "A Study of Things",
        "publication_year": 2024,
        "venue": "Journal of Things",
        "volume": "12",
        "pages": "1-10",
        "doi": "10.1234/things.2024.001",
        "citation_text": None,
        "created_at": None,
        "lecturer_ids": [uuid4()],
    }
    return PublicationResponse(**(values | overrides))


def one_page(*items: PublicationResponse) -> PageResponse[PublicationResponse]:
    return PageResponse[PublicationResponse](
        items=list(items), meta=PageMeta(total=len(items), limit=20, offset=0)
    )


def test_list_publications(client: TestClient, service: MagicMock) -> None:
    service.list_publications.return_value = one_page(make_publication())

    response = client.get(BASE, params={"publication_year": 2024})

    assert response.status_code == 200
    service.list_publications.assert_called_once_with(PublicationListQuery(publication_year=2024))


def test_create_publication(client: TestClient, service: MagicMock) -> None:
    service.create_publication.return_value = make_publication()

    response = client.post(BASE, json={"title": "A Study of Things", "lecturer_ids": []})

    assert response.status_code == 201


def test_create_publication_requires_title(client: TestClient, service: MagicMock) -> None:
    response = client.post(BASE, json={"venue": "Somewhere"})

    assert response.status_code == 422
    service.create_publication.assert_not_called()


def test_get_publication(client: TestClient, service: MagicMock) -> None:
    service.get_publication.return_value = make_publication(publication_id=9)

    response = client.get(f"{BASE}/9")

    assert response.status_code == 200
    service.get_publication.assert_called_once_with(9)


def test_get_unknown_publication_is_404(client: TestClient, service: MagicMock) -> None:
    service.get_publication.side_effect = NotFoundError("Publication not found")

    response = client.get(f"{BASE}/9")

    assert response.status_code == 404


def test_update_publication(client: TestClient, service: MagicMock) -> None:
    service.update_publication.return_value = make_publication(title="Renamed")

    response = client.patch(f"{BASE}/9", json={"title": "Renamed"})

    assert response.status_code == 200


def test_delete_publication(client: TestClient, service: MagicMock) -> None:
    response = client.delete(f"{BASE}/9")

    assert response.status_code == 204
    service.delete_publication.assert_called_once_with(9)


def test_list_lecturer_publications(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_publications.return_value = one_page(make_publication())

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/publications", params={"limit": 10})

    assert response.status_code == 200
    service.list_lecturer_publications.assert_called_once_with(
        lecturer_id, PublicationListQuery(limit=10)
    )
