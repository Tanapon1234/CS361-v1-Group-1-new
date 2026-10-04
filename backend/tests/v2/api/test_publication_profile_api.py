from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.core.database import get_session
from app.v2.dependencies import get_publication_profile_service
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.publication_profile_dto import PublicationProfileResponse
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication_profile import PublicationProfile
from app.v2.services.publication_profile_service import PublicationProfileService


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(PublicationProfileService, instance=True)
    app.dependency_overrides[get_publication_profile_service] = lambda: service
    return service


def profile(lecturer_id: UUID, publication_profile_id: int = 1) -> PublicationProfileResponse:
    return PublicationProfileResponse(
        publication_profile_id=publication_profile_id,
        lecturer_id=lecturer_id,
        provider="ORCID",
        url="https://orcid.org/0000-0002-1825-0097",
    )


def test_list_publication_profiles(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_publication_profiles.return_value = ListResponse[PublicationProfileResponse](
        items=[profile(lecturer_id)], meta=ListMeta(count=1)
    )

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/publication-profiles")

    assert response.status_code == 200
    assert response.json()["items"][0]["provider"] == "ORCID"
    service.list_publication_profiles.assert_called_once_with(lecturer_id)


def test_list_publication_profiles_reads_only_requested_lecturer(app: FastAPI) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    PublicationProfile.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="สมชาย",
                    email="somchai@example.ac.th",
                    is_active=False,
                ),
                Lecturer(
                    lecturer_id=other_lecturer_id,
                    name_th="สมหญิง",
                    email="somying@example.ac.th",
                ),
                PublicationProfile(
                    publication_profile_id=2,
                    lecturer_id=lecturer_id,
                    provider="ORCID",
                    url="https://orcid.org/0000-0002-1825-0097",
                ),
                PublicationProfile(
                    publication_profile_id=1,
                    lecturer_id=lecturer_id,
                    provider="Google Scholar",
                    url="https://scholar.google.com/citations?user=abc",
                ),
                PublicationProfile(
                    publication_profile_id=3,
                    lecturer_id=other_lecturer_id,
                    provider="Scopus",
                    url="https://www.scopus.com/authid/detail.uri?authorId=123",
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_profile_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        response = client.get(f"/api/v2/lecturers/{lecturer_id}/publication-profiles")

    assert response.status_code == 200
    assert [item["provider"] for item in response.json()["items"]] == [
        "Google Scholar",
        "ORCID",
    ]
    assert response.json()["meta"] == {"count": 2}


def test_list_publication_profiles_returns_empty_list_for_existing_lecturer(
    app: FastAPI,
) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    PublicationProfile.__table__.create(engine)
    with Session(engine) as session, session.begin():
        session.add(
            Lecturer(
                lecturer_id=lecturer_id,
                name_th="สมชาย",
                email="somchai@example.ac.th",
            )
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_profile_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        empty_response = client.get(f"/api/v2/lecturers/{lecturer_id}/publication-profiles")
        missing_response = client.get(f"/api/v2/lecturers/{uuid4()}/publication-profiles")

    assert empty_response.status_code == 200
    assert empty_response.json() == {"items": [], "meta": {"count": 0}}
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Lecturer not found"


def test_list_publication_profiles_rejects_invalid_lecturer_id(
    client: TestClient, service: MagicMock
) -> None:
    response = client.get("/api/v2/lecturers/not-a-uuid/publication-profiles")

    assert response.status_code == 422
    service.list_publication_profiles.assert_not_called()


def test_create_publication_profile(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.create_publication_profile.return_value = profile(lecturer_id)

    response = client.post(
        f"/api/v2/lecturers/{lecturer_id}/publication-profiles",
        json={"provider": "ORCID", "url": "https://orcid.org/0000-0002-1825-0097"},
    )

    assert response.status_code == 201
    _, data = service.create_publication_profile.call_args.args
    assert data.provider == "ORCID"
    assert data.url == "https://orcid.org/0000-0002-1825-0097"


def test_create_publication_profile_requires_provider_and_url(
    client: TestClient, service: MagicMock
) -> None:
    response = client.post(f"/api/v2/lecturers/{uuid4()}/publication-profiles", json={})

    assert response.status_code == 422
    fields = {error["field"] for error in response.json()["errors"]}
    assert fields == {"body.provider", "body.url"}


@pytest.mark.parametrize(
    "body",
    [
        {"provider": "", "url": "https://example.com"},
        {"provider": "   ", "url": "https://example.com"},
        {"provider": "x" * 101, "url": "https://example.com"},
        {"provider": "ORCID", "url": ""},
        {"provider": "ORCID", "url": "not-a-url"},
        {"provider": "ORCID", "url": "ftp://example.com/profile"},
        {"provider": "ORCID", "url": "javascript:alert(1)"},
        {"provider": "ORCID", "url": "https://example.com", "unknown": True},
    ],
    ids=[
        "empty-provider",
        "blank-provider",
        "provider-too-long",
        "empty-url",
        "invalid-url",
        "ftp-url",
        "javascript-url",
        "unknown-field",
    ],
)
def test_create_publication_profile_validates_body(
    client: TestClient, service: MagicMock, body: dict[str, Any]
) -> None:
    response = client.post(f"/api/v2/lecturers/{uuid4()}/publication-profiles", json=body)

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    service.create_publication_profile.assert_not_called()


def test_create_publication_profile_rejects_invalid_lecturer_id(
    client: TestClient, service: MagicMock
) -> None:
    response = client.post(
        "/api/v2/lecturers/not-a-uuid/publication-profiles",
        json={"provider": "ORCID", "url": "https://orcid.org/0000-0002-1825-0097"},
    )

    assert response.status_code == 422
    service.create_publication_profile.assert_not_called()


def test_post_publication_profile_persists_and_enforces_unique_tuple(app: FastAPI) -> None:
    lecturer_id = uuid4()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lecturer.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE publication_profile (
                    publication_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lecturer_id CHAR(32) NOT NULL,
                    provider VARCHAR(100) NOT NULL,
                    url TEXT NOT NULL,
                    UNIQUE (lecturer_id, provider, url)
                )
                """
            )
        )
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

    app.dependency_overrides.pop(get_publication_profile_service, None)
    app.dependency_overrides[get_session] = session_override

    first_payload = {
        "provider": "ORCID",
        "url": "https://orcid.org/0000-0002-1825-0097",
    }
    second_payload = {
        "provider": "ORCID",
        "url": "https://orcid.org/0000-0001-5109-3700",
    }
    with TestClient(app) as client:
        create_response = client.post(
            f"/api/v2/lecturers/{lecturer_id}/publication-profiles",
            json=first_payload,
        )
        duplicate_response = client.post(
            f"/api/v2/lecturers/{lecturer_id}/publication-profiles",
            json=first_payload,
        )
        same_provider_response = client.post(
            f"/api/v2/lecturers/{lecturer_id}/publication-profiles",
            json=second_payload,
        )
        missing_lecturer_response = client.post(
            f"/api/v2/lecturers/{uuid4()}/publication-profiles",
            json=first_payload,
        )

    assert create_response.status_code == 201
    assert create_response.json()["provider"] == "ORCID"
    assert create_response.json()["url"] == first_payload["url"]
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Publication profile already exists"
    assert same_provider_response.status_code == 201
    assert same_provider_response.json()["url"] == second_payload["url"]
    assert missing_lecturer_response.status_code == 404
    assert missing_lecturer_response.json()["detail"] == "Lecturer not found"

    with Session(engine) as session:
        profiles = session.exec(select(PublicationProfile)).all()
    assert len(profiles) == 2


def test_update_publication_profile(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.update_publication_profile.return_value = profile(lecturer_id, 4)

    response = client.patch(
        f"/api/v2/lecturers/{lecturer_id}/publication-profiles/4", json={"provider": "Scopus"}
    )

    assert response.status_code == 200


def test_delete_publication_profile(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/publication-profiles/4")

    assert response.status_code == 204
    service.delete_publication_profile.assert_called_once_with(lecturer_id, 4)
