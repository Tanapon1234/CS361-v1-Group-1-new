from collections.abc import Iterator
from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

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


def test_create_publication_profile(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.create_publication_profile.return_value = profile(lecturer_id)

    response = client.post(
        f"/api/v2/lecturers/{lecturer_id}/publication-profiles",
        json={"provider": "ORCID", "url": "https://orcid.org/0000-0002-1825-0097"},
    )

    assert response.status_code == 201


def test_create_publication_profile_requires_provider_and_url(
    client: TestClient, service: MagicMock
) -> None:
    response = client.post(f"/api/v2/lecturers/{uuid4()}/publication-profiles", json={})

    assert response.status_code == 422
    fields = {error["field"] for error in response.json()["errors"]}
    assert fields == {"body.provider", "body.url"}


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
    assert response.content == b""
    service.delete_publication_profile.assert_called_once_with(lecturer_id, 4)


@pytest.mark.parametrize(
    ("lecturer_id", "publication_profile_id"),
    [
        ("not-a-uuid", "1"),
        (str(uuid4()), "abc"),
        (str(uuid4()), "0"),
        (str(uuid4()), "32768"),
    ],
    ids=["invalid-lecturer-id", "invalid-profile-id", "zero-profile-id", "large-profile-id"],
)
def test_delete_publication_profile_validates_path_ids(
    client: TestClient,
    service: MagicMock,
    lecturer_id: str,
    publication_profile_id: str,
) -> None:
    response = client.delete(
        f"/api/v2/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}"
    )

    assert response.status_code == 422
    service.delete_publication_profile.assert_not_called()


def test_delete_publication_profile_persists_and_enforces_ownership(app: FastAPI) -> None:
    lecturer_id = uuid4()
    other_lecturer_id = uuid4()
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
        session.add_all(
            [
                Lecturer(
                    lecturer_id=lecturer_id,
                    name_th="สมชาย",
                    email="somchai@example.ac.th",
                ),
                Lecturer(
                    lecturer_id=other_lecturer_id,
                    name_th="สมหญิง",
                    email="somying@example.ac.th",
                ),
                PublicationProfile(
                    publication_profile_id=1,
                    lecturer_id=lecturer_id,
                    provider="ORCID",
                    url="https://orcid.org/0000-0002-1825-0097",
                ),
                PublicationProfile(
                    publication_profile_id=2,
                    lecturer_id=other_lecturer_id,
                    provider="Google Scholar",
                    url="https://scholar.google.com/citations?user=xyz",
                ),
            ]
        )

    def session_override() -> Iterator[Session]:
        with Session(engine) as session, session.begin():
            yield session

    app.dependency_overrides.pop(get_publication_profile_service, None)
    app.dependency_overrides[get_session] = session_override

    with TestClient(app) as client:
        delete_response = client.delete(f"/api/v2/lecturers/{lecturer_id}/publication-profiles/1")
        repeated_response = client.delete(f"/api/v2/lecturers/{lecturer_id}/publication-profiles/1")
        wrong_owner_response = client.delete(
            f"/api/v2/lecturers/{lecturer_id}/publication-profiles/2"
        )
        missing_lecturer_response = client.delete(
            f"/api/v2/lecturers/{uuid4()}/publication-profiles/2"
        )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert repeated_response.status_code == 404
    assert repeated_response.json()["detail"] == "Publication profile not found"
    assert wrong_owner_response.status_code == 404
    assert wrong_owner_response.json()["detail"] == "Publication profile not found"
    assert missing_lecturer_response.status_code == 404
    assert missing_lecturer_response.json()["detail"] == "Lecturer not found"

    with Session(engine) as session:
        deleted = session.get(PublicationProfile, 1)
        other = session.get(PublicationProfile, 2)
    assert deleted is None
    assert other is not None
    assert other.lecturer_id == other_lecturer_id
