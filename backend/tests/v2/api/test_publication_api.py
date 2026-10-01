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
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.dependencies import get_publication_service
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import (
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateResponse,
)
from app.v2.models.publication import Publication
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
    service.update_publication.return_value = PublicationUpdateResponse(
        publication_id=1,
        title="A New Mobile Application",
        publication_year=2018,
        venue="Hospital Pediatrics",
        volume="9",
        pages="100-110",
        doi="10.1542/hpeds.2018-0073",
        citation_text="Wantanakorn, Pornchanok & ...",
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    response = client.patch(
        f"{BASE}/1",
        json={"volume": "9", "pages": "100-110"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "publication_id": 1,
        "title": "A New Mobile Application",
        "publication_year": 2018,
        "venue": "Hospital Pediatrics",
        "volume": "9",
        "pages": "100-110",
        "doi": "10.1542/hpeds.2018-0073",
        "citation_text": "Wantanakorn, Pornchanok & ...",
        "created_at": "2026-10-01T00:00:00Z",
    }
    publication_id, data = service.update_publication.call_args.args
    assert publication_id == 1
    assert data.model_dump(exclude_unset=True) == {
        "volume": "9",
        "pages": "100-110",
    }


def test_update_publication_invalid_id_is_422(client: TestClient, service: MagicMock) -> None:
    response = client.patch(f"{BASE}/abc", json={"volume": "9"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.update_publication.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": None},
        {"volume": "x" * 51},
        {"lecturer_ids": []},
    ],
    ids=["empty-title", "null-title", "long-volume", "unknown-field"],
)
def test_update_publication_invalid_body_is_422(
    client: TestClient, service: MagicMock, body: dict[str, Any]
) -> None:
    response = client.patch(f"{BASE}/1", json=body)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.update_publication.assert_not_called()


def test_update_unknown_publication_is_404(client: TestClient, service: MagicMock) -> None:
    service.update_publication.side_effect = NotFoundError("Publication not found")

    response = client.patch(f"{BASE}/999999", json={"volume": "9"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_update_publication_duplicate_doi_is_409(client: TestClient, service: MagicMock) -> None:
    service.update_publication.side_effect = ConflictError("Publication DOI already exists")

    response = client.patch(f"{BASE}/1", json={"doi": "10.1000/duplicate"})

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")


def test_update_publication_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.update_publication.side_effect = ServiceUnavailableError("Database is unreachable")

    response = client.patch(f"{BASE}/1", json={"volume": "9"})

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


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


def test_update_publication_persists_partial_fields_and_rejects_duplicate_doi(
    app: FastAPI,
) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Publication.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Publication(
                    publication_id=1,
                    title="A New Mobile Application",
                    publication_year=2018,
                    venue="Hospital Pediatrics",
                    volume="8",
                    pages=None,
                    doi="10.1542/hpeds.2018-0073",
                    citation_text="Wantanakorn, Pornchanok & ...",
                    created_at=datetime(2026, 10, 1, tzinfo=UTC),
                ),
                Publication(
                    publication_id=2,
                    title="Another publication",
                    publication_year=2020,
                    doi="10.1000/duplicate",
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        update_response = client.patch(
            f"{BASE}/1",
            json={"volume": "9", "pages": "100-110"},
        )
        duplicate_response = client.patch(
            f"{BASE}/1",
            json={"doi": "10.1000/duplicate"},
        )
        unknown_response = client.patch(
            f"{BASE}/999999",
            json={"volume": "9"},
        )

    assert update_response.status_code == 200
    assert update_response.json()["volume"] == "9"
    assert update_response.json()["pages"] == "100-110"
    assert update_response.json()["title"] == "A New Mobile Application"
    assert update_response.json()["venue"] == "Hospital Pediatrics"
    assert "lecturer_ids" not in update_response.json()
    assert duplicate_response.status_code == 409
    assert unknown_response.status_code == 404

    with Session(engine) as session:
        publication = session.exec(select(Publication).where(Publication.publication_id == 1)).one()
    assert publication.volume == "9"
    assert publication.pages == "100-110"
    assert publication.doi == "10.1542/hpeds.2018-0073"
