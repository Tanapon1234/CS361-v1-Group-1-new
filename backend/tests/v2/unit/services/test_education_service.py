"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.education_dao import EducationDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.services.education_service import EducationService

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement EducationService"
)


@pytest.fixture
def education_dao() -> MagicMock:
    return create_autospec(EducationDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(education_dao: MagicMock, lecturer_dao: MagicMock) -> EducationService:
    return EducationService(education_dao, lecturer_dao)


def test_list_for_unknown_lecturer_raises_not_found(
    service: EducationService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.list_educations(uuid4())
