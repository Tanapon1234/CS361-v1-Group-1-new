"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_profile_dao import PublicationProfileDAO
from app.v2.services.publication_profile_service import PublicationProfileService

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement PublicationProfileService"
)


@pytest.fixture
def publication_profile_dao() -> MagicMock:
    return create_autospec(PublicationProfileDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(
    publication_profile_dao: MagicMock, lecturer_dao: MagicMock
) -> PublicationProfileService:
    return PublicationProfileService(publication_profile_dao, lecturer_dao)


def test_list_for_unknown_lecturer_raises_not_found(
    service: PublicationProfileService, lecturer_dao: MagicMock
) -> None:
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.list_publication_profiles(uuid4())
