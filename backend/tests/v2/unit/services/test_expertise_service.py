"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.services.expertise_service import ExpertiseService

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement ExpertiseService"
)


@pytest.fixture
def expertise_dao() -> MagicMock:
    return create_autospec(ExpertiseDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(expertise_dao: MagicMock, lecturer_dao: MagicMock) -> ExpertiseService:
    return ExpertiseService(expertise_dao, lecturer_dao)


def test_get_unknown_expertise_raises_not_found(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    expertise_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_expertise(99)
