from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.v2.dependencies import get_lecturer_work_service
from app.v2.dtos.lecturer_work_dto import LecturerWorkFilters, LecturerWorkResponse
from app.v2.services.lecturer_work_service import LecturerWorkService


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(LecturerWorkService, instance=True)
    app.dependency_overrides[get_lecturer_work_service] = lambda: service
    return service


def test_get_work_passes_the_filters(client: TestClient, service: MagicMock) -> None:
    lecturer_id = uuid4()
    service.get_work.return_value = LecturerWorkResponse(
        lecturer_id=lecturer_id,
        lecturer_name_th="สมชาย",
        filters=LecturerWorkFilters(academic_year=2567, category="2", category_name_th=None),
        categories=[],
        publications=[],
        total=0,
        available_years=[],
    )

    response = client.get(
        f"/api/v2/lecturers/{lecturer_id}/work", params={"academic_year": 2567, "category": "2"}
    )

    assert response.status_code == 200
    assert response.json()["filters"]["academic_year"] == 2567
    called_id, _, query = service.get_work.call_args.args
    assert (called_id, query.academic_year, query.category) == (lecturer_id, 2567, "2")


@pytest.mark.parametrize(
    "params",
    [{"academic_year": 2024}, {"academic_year": "x"}, {"category": "toolong"}],
    ids=["ce-year", "not-a-number", "long-category"],
)
def test_invalid_filters_are_422(client: TestClient, service: MagicMock, params: dict) -> None:
    response = client.get(f"/api/v2/lecturers/{uuid4()}/work", params=params)

    assert response.status_code == 422
    service.get_work.assert_not_called()
