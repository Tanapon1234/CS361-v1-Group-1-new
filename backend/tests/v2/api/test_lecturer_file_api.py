"""Profile image and CV endpoints (LecturerFileService)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.v2.dependencies import get_lecturer_file_service
from app.v2.dtos.lecturer_dto import LecturerResponse
from app.v2.dtos.lecturer_file_dto import FileDownloadResponse, UploadPresignResponse
from app.v2.services.lecturer_file_service import LecturerFileService

PRESIGN_BODY = {"content_type": "application/pdf", "size_bytes": 1024}


@pytest.fixture
def service(app: FastAPI) -> MagicMock:
    service = create_autospec(LecturerFileService, instance=True)
    app.dependency_overrides[get_lecturer_file_service] = lambda: service
    return service


def presigned() -> UploadPresignResponse:
    return UploadPresignResponse(
        upload_url="https://bucket.s3.amazonaws.com/",
        object_key="lecturers/x/file",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )


def lecturer() -> LecturerResponse:
    return LecturerResponse(
        lecturer_id=uuid4(),
        name_th="สมชาย",
        name_en=None,
        rank=None,
        profile_image_url="https://bucket.s3.amazonaws.com/lecturers/x/file",
        office=None,
        phone=None,
        phone_extension=None,
        email="somchai@example.ac.th",
        is_active=True,
        created_at=None,
        updated_at=None,
    )


@pytest.mark.parametrize(
    ("segment", "method"),
    [("profile-image", "create_profile_image_upload"), ("cv", "create_cv_upload")],
)
def test_presign(client: TestClient, service: MagicMock, segment: str, method: str) -> None:
    lecturer_id = uuid4()
    getattr(service, method).return_value = presigned()

    response = client.post(f"/api/v2/lecturers/{lecturer_id}/{segment}/presign", json=PRESIGN_BODY)

    assert response.status_code == 200
    assert response.json()["object_key"] == "lecturers/x/file"
    assert getattr(service, method).call_args.args[0] == lecturer_id


def test_presign_requires_positive_size(client: TestClient, service: MagicMock) -> None:
    response = client.post(
        f"/api/v2/lecturers/{uuid4()}/cv/presign",
        json={"content_type": "application/pdf", "size_bytes": 0},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("segment", "method"),
    [("profile-image", "complete_profile_image_upload"), ("cv", "complete_cv_upload")],
)
def test_complete(client: TestClient, service: MagicMock, segment: str, method: str) -> None:
    getattr(service, method).return_value = lecturer()

    response = client.post(
        f"/api/v2/lecturers/{uuid4()}/{segment}/complete", json={"object_key": "lecturers/x/file"}
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("segment", "method"), [("profile-image", "delete_profile_image"), ("cv", "delete_cv")]
)
def test_delete(client: TestClient, service: MagicMock, segment: str, method: str) -> None:
    lecturer_id = uuid4()

    response = client.delete(f"/api/v2/lecturers/{lecturer_id}/{segment}")

    assert response.status_code == 204
    getattr(service, method).assert_called_once_with(lecturer_id)


def test_get_cv(client: TestClient, service: MagicMock) -> None:
    service.get_cv.return_value = FileDownloadResponse(
        download_url="https://bucket.s3.amazonaws.com/cv.pdf?sig=abc",
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    response = client.get(f"/api/v2/lecturers/{uuid4()}/cv")

    assert response.status_code == 200
    assert response.json()["download_url"].startswith("https://")
