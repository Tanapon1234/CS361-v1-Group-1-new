from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.v2.dependencies import get_publication_profile_service
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.publication_profile_dto import PublicationProfileResponse
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
    service.delete_publication_profile.assert_called_once_with(lecturer_id, 4)
