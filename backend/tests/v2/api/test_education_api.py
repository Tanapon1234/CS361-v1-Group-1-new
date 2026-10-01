from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.v2.dependencies import get_education_service
from app.v2.dtos.common import ListMeta, ListResponse
from app.v2.dtos.education_dto import EducationResponse
from app.v2.services.education_service import EducationService


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(EducationService, instance=True)
    app.dependency_overrides[get_education_service] = lambda: service
    return service


def make_education(lecturer_id: UUID, education_id: int = 1) -> EducationResponse:
    return EducationResponse(
        education_id=education_id,
        lecturer_id=lecturer_id,
        degree="Ph.D.",
        field="Computer Science",
        institution="Example University",
        country="Thailand",
        graduation_year="2555",
    )


def test_list_educations(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.list_educations.return_value = ListResponse[EducationResponse](
        items=[make_education(lecturer_id)], meta=ListMeta(count=1)
    )

    response = client.get(f"/api/v2/lecturers/{lecturer_id}/educations")

    assert response.status_code == 200
    assert response.json()["meta"] == {"count": 1}


def test_create_education(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.create_education.return_value = make_education(lecturer_id)

    response = client.post(
        f"/api/v2/lecturers/{lecturer_id}/educations",
        json={"degree": "Ph.D.", "institution": "Example University"},
    )

    assert response.status_code == 201


def test_update_education(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.update_education.return_value = make_education(lecturer_id, education_id=7)

    response = client.patch(
        f"/api/v2/lecturers/{lecturer_id}/educations/7", json={"country": "Japan"}
    )

    assert response.status_code == 200
    assert service.update_education.call_args.args[:2] == (lecturer_id, 7)


def test_delete_education(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/educations/7")

    assert response.status_code == 204
    service.delete_education.assert_called_once_with(lecturer_id, 7)


@pytest.mark.parametrize("education_id", ["abc", "0", "40000"])
def test_education_id_must_be_a_smallint(
    client: TestClient, service: MagicMock, education_id: str
) -> None:
    response = client.delete(f"/api/v2/lecturers/{uuid4()}/educations/{education_id}")

    assert response.status_code == 422
    service.delete_education.assert_not_called()
