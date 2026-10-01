"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.services.publication_service import PublicationService

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement PublicationService"
)


@pytest.fixture
def publication_dao() -> MagicMock:
    return create_autospec(PublicationDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(publication_dao: MagicMock, lecturer_dao: MagicMock) -> PublicationService:
    return PublicationService(publication_dao, lecturer_dao)


def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_publication(99)
