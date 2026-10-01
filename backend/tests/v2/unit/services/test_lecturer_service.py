"""Service tests with a mocked DAO. One example to start from; add tests for your own rules.

While the service raises NotImplementedError the test reports XFAIL. Once it passes it
reports XPASS and fails the run on purpose: delete the `pytestmark` line then.
"""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.services.lecturer_service import LecturerService

pytestmark = pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement LecturerService")


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(lecturer_dao: MagicMock) -> LecturerService:
    return LecturerService(lecturer_dao)


def test_get_unknown_lecturer_raises_not_found(
    service: LecturerService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_lecturer(uuid4())
