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
    LecturerPublicationResponse,
    PublicationListItemResponse,
    PublicationListQuery,
    PublicationResponse,
    PublicationUpdateResponse,
)
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import FacultyPublication, Publication
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


def lecturer_publication_page(
    *items: LecturerPublicationResponse,
    total: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> PageResponse[LecturerPublicationResponse]:
    return PageResponse[LecturerPublicationResponse](
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
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    service.create_publication.return_value = PublicationListItemResponse(
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
    assert response.content == b""
    service.delete_publication.assert_called_once_with(9)


def test_delete_unknown_publication_is_404(client: TestClient, service: MagicMock) -> None:
    service.delete_publication.side_effect = NotFoundError("Publication not found")

    response = client.delete(f"{BASE}/999999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_delete_invalid_publication_id_is_422(client: TestClient, service: MagicMock) -> None:
    response = client.delete(f"{BASE}/abc")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    service.delete_publication.assert_not_called()


def test_delete_publication_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.delete_publication.side_effect = ServiceUnavailableError("Database unavailable")

    response = client.delete(f"{BASE}/9")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


def test_delete_publication_cascades_authorship_and_keeps_lecturer(app: FastAPI) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
    Lecturer.__table__.create(engine)
    Publication.__table__.create(engine)
    FacultyPublication.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="Somchai",
                    email="somchai@example.ac.th",
                ),
                Publication(publication_id=1, title="Deleted publication"),
            ]
        )
        session.flush()
        session.add(
            FacultyPublication(
                lecturer_id=lecturer_id,
                publication_id=1,
                author_order=1,
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        response = client.delete(f"{BASE}/1")

    assert response.status_code == 204
    assert response.content == b""
    with Session(engine) as session:
        assert session.get(Publication, 1) is None
        assert session.get(Lecturer, lecturer_id) is not None
        assert session.exec(select(FacultyPublication)).all() == []


def test_list_lecturer_publications(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_publications.return_value = lecturer_publication_page(
        LecturerPublicationResponse(
            **list_item().model_dump(),
            author_order=5,
        ),
        limit=10,
    )

    response = client.get(
        f"/api/v2/lecturers/{lecturer_id}/publications",
        params={"q": "mobile", "publication_year": 2018, "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["author_order"] == 5
    assert response.json()["meta"] == {"total": 1, "limit": 10, "offset": 0}
    service.list_lecturer_publications.assert_called_once_with(
        lecturer_id,
        PublicationListQuery(q="mobile", publication_year=2018, limit=10, offset=0),
    )


def test_list_lecturer_publications_empty(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_lecturer_publications.return_value = lecturer_publication_page()

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/publications")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }


def test_list_lecturer_publications_invalid_uuid_is_422(
    client: TestClient, service: MagicMock
) -> None:
    response = client.get("/api/v2/lecturers/not-a-uuid/publications")

    assert response.status_code == 422
    service.list_lecturer_publications.assert_not_called()


@pytest.mark.parametrize(
    "params",
    [{"limit": "101"}, {"offset": "-1"}],
    ids=["limit-too-large", "negative-offset"],
)
def test_list_lecturer_publications_invalid_query_is_422(
    client: TestClient, service: MagicMock, params: dict[str, str]
) -> None:
    response = client.get(f"/api/v2/lecturers/{uuid4()}/publications", params=params)

    assert response.status_code == 422
    service.list_lecturer_publications.assert_not_called()


def test_list_lecturer_publications_unknown_lecturer_is_404(
    client: TestClient, service: MagicMock
) -> None:
    service.list_lecturer_publications.side_effect = NotFoundError("Lecturer not found")

    response = client.get(f"/api/v2/lecturers/{uuid4()}/publications")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


def test_list_lecturer_publications_database_unavailable_is_503(
    client: TestClient, service: MagicMock
) -> None:
    service.list_lecturer_publications.side_effect = ServiceUnavailableError(
        "Database is unreachable"
    )

    response = client.get(f"/api/v2/lecturers/{uuid4()}/publications")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


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


def test_list_lecturer_publications_filters_scope_and_author_order(
    app: FastAPI,
) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
    empty_lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    Publication.__table__.create(engine)
    FacultyPublication.__table__.create(engine)
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
                Lecturer(
                    lecturer_id=empty_lecturer_id,
                    name_th="Somsak",
                    email="somsak@example.ac.th",
                ),
                Publication(
                    publication_id=1,
                    title="A New Mobile Application",
                    publication_year=2018,
                    venue="Hospital Pediatrics",
                    doi="10.1542/hpeds.2018-0073",
                ),
                Publication(
                    publication_id=2,
                    title="Pediatric Anxiety Research",
                    publication_year=2018,
                    venue="Health Journal",
                    doi="10.1000/pediatric",
                ),
                Publication(
                    publication_id=3,
                    title="Computer Vision",
                    publication_year=2020,
                    venue="AI Journal",
                    doi="10.1000/vision",
                ),
            ]
        )
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                FacultyPublication(
                    lecturer_id=lecturer_id,
                    publication_id=1,
                    author_order=5,
                ),
                FacultyPublication(
                    lecturer_id=lecturer_id,
                    publication_id=2,
                    author_order=2,
                ),
                FacultyPublication(
                    lecturer_id=other_lecturer_id,
                    publication_id=3,
                    author_order=1,
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_service, None)
    app.dependency_overrides[get_session] = session_override
    lecturer_url = f"/api/v2/lecturers/{lecturer_id}/publications"

    with TestClient(app) as client:
        all_response = client.get(lecturer_url)
        q_response = client.get(lecturer_url, params={"q": "MOBILE"})
        year_response = client.get(lecturer_url, params={"publication_year": 2018})
        combined_response = client.get(
            lecturer_url,
            params={"q": "MOBILE", "publication_year": 2018},
        )
        paged_response = client.get(
            lecturer_url,
            params={"limit": 1, "offset": 1},
        )
        empty_response = client.get(f"/api/v2/lecturers/{empty_lecturer_id}/publications")
        unknown_response = client.get(f"/api/v2/lecturers/{uuid4()}/publications")

    assert all_response.status_code == 200
    assert [item["publication_id"] for item in all_response.json()["items"]] == [2, 1]
    assert [item["author_order"] for item in all_response.json()["items"]] == [2, 5]
    assert all_response.json()["meta"]["total"] == 2
    assert [item["publication_id"] for item in q_response.json()["items"]] == [1]
    assert [item["publication_id"] for item in year_response.json()["items"]] == [2, 1]
    assert [item["publication_id"] for item in combined_response.json()["items"]] == [1]
    assert [item["publication_id"] for item in paged_response.json()["items"]] == [1]
    assert paged_response.json()["meta"] == {"total": 2, "limit": 1, "offset": 1}
    assert empty_response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }
    assert unknown_response.status_code == 404


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
