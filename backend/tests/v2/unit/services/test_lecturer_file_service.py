from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.lecturer_file_dto import UploadCompleteRequest, UploadPresignRequest
from app.v2.models.lecturer import Lecturer
from app.v2.services.lecturer_file_service import LecturerFileService
from app.v2.storage.object_storage import (
    ObjectStorage,
    PresignedDownload,
    PresignedUpload,
    StoredObject,
)

LECTURER_ID = uuid4()
IMAGE_PREFIX = f"lecturers/{LECTURER_ID}/profile-image/"
CV_PREFIX = f"lecturers/{LECTURER_ID}/cv/"


@pytest.fixture
def lecturer() -> Lecturer:
    return Lecturer(lecturer_id=LECTURER_ID, name_th="สมชาย", email="somchai@example.ac.th")


@pytest.fixture
def lecturer_dao(lecturer: Lecturer) -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.return_value = lecturer
    dao.update.side_effect = lambda row, values: row.sqlmodel_update(values) or row
    return dao


@pytest.fixture
def storage() -> MagicMock:
    storage = create_autospec(ObjectStorage, instance=True)
    storage.create_presigned_upload.return_value = PresignedUpload(
        url="https://bucket.s3.amazonaws.com/", fields={"key": "k"}, expires_at=datetime.now(UTC)
    )
    storage.create_presigned_download.return_value = PresignedDownload(
        url="https://bucket.s3.amazonaws.com/signed", expires_at=datetime.now(UTC)
    )
    return storage


@pytest.fixture
def service(lecturer_dao: MagicMock, storage: MagicMock) -> LecturerFileService:
    return LecturerFileService(lecturer_dao, storage, Settings(_env_file=None))  # type: ignore[call-arg]


def test_get_cv_of_unknown_lecturer_raises_not_found(
    service: LecturerFileService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_cv(uuid4())


def test_presign_image_puts_the_key_under_the_lecturer(
    service: LecturerFileService, storage: MagicMock
) -> None:
    result = service.create_profile_image_upload(
        LECTURER_ID, UploadPresignRequest(content_type="image/png", size_bytes=1000)
    )

    assert result.object_key.startswith(IMAGE_PREFIX)
    assert result.object_key.endswith(".png")
    assert storage.create_presigned_upload.call_args.kwargs["content_type"] == "image/png"


@pytest.mark.parametrize(
    ("content_type", "size"),
    [("application/pdf", 1000), ("image/png", 50 * 1024 * 1024)],
    ids=["wrong-type", "too-big"],
)
def test_presign_image_rejects_bad_files(
    service: LecturerFileService, content_type: str, size: int
) -> None:
    with pytest.raises(BadRequestError):
        service.create_profile_image_upload(
            LECTURER_ID, UploadPresignRequest(content_type=content_type, size_bytes=size)
        )


def test_presign_cv_only_takes_pdf(service: LecturerFileService) -> None:
    with pytest.raises(BadRequestError):
        service.create_cv_upload(
            LECTURER_ID, UploadPresignRequest(content_type="image/png", size_bytes=1000)
        )


def test_complete_rejects_a_key_of_another_lecturer(
    service: LecturerFileService, storage: MagicMock
) -> None:
    with pytest.raises(BadRequestError):
        service.complete_cv_upload(
            LECTURER_ID, UploadCompleteRequest(object_key=f"lecturers/{uuid4()}/cv/x.pdf")
        )
    storage.head_object.assert_not_called()


def test_complete_before_upload_is_rejected(
    service: LecturerFileService, storage: MagicMock
) -> None:
    storage.head_object.return_value = None

    with pytest.raises(BadRequestError):
        service.complete_cv_upload(
            LECTURER_ID, UploadCompleteRequest(object_key=f"{CV_PREFIX}a.pdf")
        )


def test_complete_saves_the_key_and_removes_the_old_file(
    service: LecturerFileService, storage: MagicMock, lecturer: Lecturer
) -> None:
    lecturer.cv_url = f"{CV_PREFIX}old.pdf"
    new_key = f"{CV_PREFIX}new.pdf"
    storage.head_object.return_value = StoredObject(
        key=new_key, size_bytes=1000, content_type="application/pdf"
    )

    service.complete_cv_upload(LECTURER_ID, UploadCompleteRequest(object_key=new_key))

    assert lecturer.cv_url == new_key
    storage.delete_object.assert_called_once_with(f"{CV_PREFIX}old.pdf")


def test_get_cv_signs_a_stored_file(
    service: LecturerFileService, storage: MagicMock, lecturer: Lecturer
) -> None:
    lecturer.cv_url = f"{CV_PREFIX}a.pdf"

    result = service.get_cv(LECTURER_ID)

    assert result.download_url == "https://bucket.s3.amazonaws.com/signed"
    assert storage.create_presigned_download.call_args.kwargs["file_name"] == "cv-สมชาย.pdf"


def test_get_image_returns_an_external_v1_url_as_is(
    service: LecturerFileService, storage: MagicMock, lecturer: Lecturer
) -> None:
    lecturer.profile_image_url = "https://cs.tu.ac.th/img/somchai.jpg"

    result = service.get_profile_image(LECTURER_ID)

    assert result.download_url == "https://cs.tu.ac.th/img/somchai.jpg"
    storage.create_presigned_download.assert_not_called()


def test_delete_without_a_file_is_not_found(service: LecturerFileService) -> None:
    with pytest.raises(NotFoundError):
        service.delete_profile_image(LECTURER_ID)


def test_delete_external_url_only_clears_the_column(
    service: LecturerFileService, storage: MagicMock, lecturer: Lecturer
) -> None:
    lecturer.profile_image_url = "https://cs.tu.ac.th/img/somchai.jpg"

    service.delete_profile_image(LECTURER_ID)

    assert lecturer.profile_image_url is None
    storage.delete_object.assert_not_called()
