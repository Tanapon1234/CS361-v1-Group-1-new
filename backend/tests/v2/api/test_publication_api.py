from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.core.database import get_session
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.v2.dependencies import get_publication_service
from app.v2.dtos.common import PageMeta, PageResponse
from app.v2.dtos.publication_dto import (
    PublicationListItemResponse,
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


def list_item(publication_id: int = 1) -> PublicationListItemResponse:
    return PublicationListItemResponse(
        publication_id=publication_id,
        title="A New Mobile Application",
        publication_year=2018,
        venue="Hospital Pediatrics",
        volume="8",
        pages=None,
        doi="10.1542/hpeds.2018-0073",
        citation_text="Wantanakorn, Pornchanok & ...",
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )


def publication_page(
    *items: PublicationListItemResponse,
    total: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> PageResponse[PublicationListItemResponse]:
    return PageResponse[PublicationListItemResponse](
        items=list(items),
        meta=PageMeta(
            total=len(items) if total is None else total,
            limit=limit,
            offset=offset,
        ),
    )


def test_list_publications(client: TestClient, service: MagicMock) -> None:
    service.list_publications.return_value = publication_page(list_item(), limit=10, offset=20)

    response = client.get(
        BASE,
        params={"q": "mobile", "publication_year": 2018, "limit": 10, "offset": 20},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "publication_id": 1,
                "title": "A New Mobile Application",
                "publication_year": 2018,
                "venue": "Hospital Pediatrics",
                "volume": "8",
                "pages": None,
                "doi": "10.1542/hpeds.2018-0073",
                "citation_text": "Wantanakorn, Pornchanok & ...",
                "created_at": "2026-10-01T00:00:00Z",
            }
        ],
        "meta": {"total": 1, "limit": 10, "offset": 20},
    }
    service.list_publications.assert_called_once_with(
        PublicationListQuery(q="mobile", publication_year=2018, limit=10, offset=20)
    )


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "101"},
        {"offset": "-1"},
        {"publication_year": "not-a-year"},
    ],
    ids=["limit-too-large", "negative-offset", "invalid-year"],
)
def test_list_publications_invalid_query_is_422(
    client: TestClient, service: MagicMock, params: dict[str, str]
) -> None:
    response = client.get(BASE, params=params)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.list_publications.assert_not_called()


def test_list_publications_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.list_publications.side_effect = ServiceUnavailableError("Database is unreachable")

    response = client.get(BASE)

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


def test_create_publication(client: TestClient, service: MagicMock) -> None:
    service.create_publication.return_value = make_publication()

    response = client.post(BASE, json={"title": "A Study of Things", "lecturer_ids": []})

    assert response.status_code == 201


def test_create_publication_requires_title(client: TestClient, service: MagicMock) -> None:
    response = client.post(BASE, json={"venue": "Somewhere"})

    assert response.status_code == 422
    service.create_publication.assert_not_called()


def test_get_publication(client: TestClient, service: MagicMock) -> None:
    service.get_publication.return_value = list_item(publication_id=9)

    response = client.get(f"{BASE}/9")

    assert response.status_code == 200
    assert response.json() == {
        "publication_id": 9,
        "title": "A New Mobile Application",
        "publication_year": 2018,
        "venue": "Hospital Pediatrics",
        "volume": "8",
        "pages": None,
        "doi": "10.1542/hpeds.2018-0073",
        "citation_text": "Wantanakorn, Pornchanok & ...",
        "created_at": "2026-10-01T00:00:00Z",
    }
    service.get_publication.assert_called_once_with(9)


def test_get_unknown_publication_is_404(client: TestClient, service: MagicMock) -> None:
    service.get_publication.side_effect = NotFoundError("Publication not found")

    response = client.get(f"{BASE}/9")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_get_publication_invalid_id_is_422(client: TestClient, service: MagicMock) -> None:
    response = client.get(f"{BASE}/abc")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.get_publication.assert_not_called()


def test_get_publication_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.get_publication.side_effect = ServiceUnavailableError("Database is unreachable")

    response = client.get(f"{BASE}/1")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


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


def test_list_publications_search_filter_and_pagination(app: FastAPI) -> None:
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
                    doi="10.1542/hpeds.2018-0073",
                ),
                Publication(
                    publication_id=2,
                    title="Anxiety in Pediatric Patients",
                    publication_year=2018,
                    venue="Mobile Health Journal",
                    doi="10.1000/pediatric",
                ),
                Publication(
                    publication_id=3,
                    title="Computer Vision",
                    publication_year=2020,
                    venue="AI Journal",
                    doi="10.1000/MOBILE-doi",
                ),
                Publication(
                    publication_id=4,
                    title="Robotics",
                    publication_year=2021,
                    venue="Engineering Journal",
                    doi=None,
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        title_response = client.get(BASE, params={"q": "NEW mobile"})
        venue_response = client.get(BASE, params={"q": "mobile health"})
        doi_response = client.get(BASE, params={"q": "mobile-DOI"})
        year_response = client.get(BASE, params={"publication_year": 2018})
        combined_response = client.get(BASE, params={"q": "mobile", "publication_year": 2018})
        paged_response = client.get(BASE, params={"limit": 2, "offset": 1})
        empty_response = client.get(BASE, params={"q": "quantum"})

    assert [item["publication_id"] for item in title_response.json()["items"]] == [1]
    assert [item["publication_id"] for item in venue_response.json()["items"]] == [2]
    assert [item["publication_id"] for item in doi_response.json()["items"]] == [3]
    assert [item["publication_id"] for item in year_response.json()["items"]] == [1, 2]
    assert [item["publication_id"] for item in combined_response.json()["items"]] == [
        1,
        2,
    ]
    assert combined_response.json()["meta"]["total"] == 2
    assert [item["publication_id"] for item in paged_response.json()["items"]] == [
        2,
        3,
    ]
    assert paged_response.json()["meta"] == {"total": 4, "limit": 2, "offset": 1}
    assert empty_response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }


def test_get_publication_from_database_and_unknown_id(app: FastAPI) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Publication.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add(
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
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        existing_response = client.get(f"{BASE}/1")
        unknown_response = client.get(f"{BASE}/999999")

    assert existing_response.status_code == 200
    assert existing_response.json()["publication_id"] == 1
    assert existing_response.json()["pages"] is None
    assert "lecturer_ids" not in existing_response.json()
    assert unknown_response.status_code == 404
