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
    PublicationCreateResponse,
    PublicationListQuery,
    PublicationResponse,
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
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    service.create_publication.return_value = PublicationCreateResponse(
        publication_id=1,
        title="A Study of Things",
        publication_year=2018,
        venue="Hospital Pediatrics",
        volume="8",
        pages=None,
        doi="10.1542/hpeds.2018-0073",
        citation_text="Wantanakorn, Pornchanok & ...",
        created_at=created_at,
    )

    response = client.post(
        BASE,
        json={
            "title": "A Study of Things",
            "publication_year": 2018,
            "venue": "Hospital Pediatrics",
            "volume": "8",
            "pages": None,
            "doi": "10.1542/hpeds.2018-0073",
            "citation_text": "Wantanakorn, Pornchanok & ...",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "publication_id": 1,
        "title": "A Study of Things",
        "publication_year": 2018,
        "venue": "Hospital Pediatrics",
        "volume": "8",
        "pages": None,
        "doi": "10.1542/hpeds.2018-0073",
        "citation_text": "Wantanakorn, Pornchanok & ...",
        "created_at": "2026-10-01T00:00:00Z",
    }


def test_create_publication_requires_title(client: TestClient, service: MagicMock) -> None:
    response = client.post(BASE, json={"venue": "Somewhere"})

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.create_publication.assert_not_called()


def test_create_publication_rejects_invalid_field_type(
    client: TestClient, service: MagicMock
) -> None:
    response = client.post(
        BASE,
        json={"title": "Invalid publication", "publication_year": "not-a-year"},
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.create_publication.assert_not_called()


def test_create_publication_duplicate_doi_is_409(client: TestClient, service: MagicMock) -> None:
    service.create_publication.side_effect = ConflictError("Publication DOI already exists")

    response = client.post(
        BASE,
        json={"title": "Duplicate", "doi": "10.1542/hpeds.2018-0073"},
    )

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")


def test_create_publication_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.create_publication.side_effect = ServiceUnavailableError("Database unavailable")

    response = client.post(BASE, json={"title": "Unavailable publication"})

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


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


def test_create_publication_persists_and_rejects_duplicate_doi(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Publication.__table__.create(engine)

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override
    body = {
        "title": "A New Mobile Application",
        "publication_year": 2018,
        "venue": "Hospital Pediatrics",
        "volume": "8",
        "pages": None,
        "doi": "10.1542/hpeds.2018-0073",
        "citation_text": "Wantanakorn, Pornchanok & ...",
    }

    with TestClient(app) as client:
        create_response = client.post(BASE, json=body)
        duplicate_response = client.post(BASE, json=body)

    assert create_response.status_code == 201
    assert create_response.json()["publication_id"] == 1
    assert create_response.json()["pages"] is None
    assert "lecturer_ids" not in create_response.json()
    assert duplicate_response.status_code == 409
    with Session(engine) as session:
        publications = session.exec(select(Publication)).all()
    assert len(publications) == 1
    assert publications[0].doi == "10.1542/hpeds.2018-0073"


def test_create_publication_database_error_rolls_back(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Publication.__table__.create(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TRIGGER fail_publication_insert
            BEFORE INSERT ON publication
            BEGIN
                SELECT RAISE(ABORT, 'forced insert failure');
            END
            """
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(BASE, json={"title": "Failed publication"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    with Session(engine) as session:
        assert session.exec(select(Publication)).all() == []
