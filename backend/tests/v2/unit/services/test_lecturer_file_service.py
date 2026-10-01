"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.services.lecturer_file_service import LecturerFileService
from app.v2.storage.object_storage import ObjectStorage

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement LecturerFileService"
)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def storage() -> MagicMock:
    return create_autospec(ObjectStorage, instance=True)


@pytest.fixture
def service(lecturer_dao: MagicMock, storage: MagicMock) -> LecturerFileService:
    return LecturerFileService(lecturer_dao, storage, Settings(_env_file=None))  # type: ignore[call-arg]


def test_get_cv_of_unknown_lecturer_raises_not_found(
    service: LecturerFileService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_cv(uuid4())
