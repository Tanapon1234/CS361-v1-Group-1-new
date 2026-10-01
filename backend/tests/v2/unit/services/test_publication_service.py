"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.models.publication import Publication
from app.v2.services.publication_service import PublicationService


@pytest.fixture
def publication_dao() -> MagicMock:
    return create_autospec(PublicationDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(publication_dao: MagicMock, lecturer_dao: MagicMock) -> PublicationService:
    return PublicationService(publication_dao, lecturer_dao)


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement get publication")
def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_publication(99)


def test_delete_existing_publication(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication = Publication(publication_id=7, title="A Study of Things")
    publication_dao.get_by_id.return_value = publication

    result = service.delete_publication(7)

    assert result is None
    publication_dao.get_by_id.assert_called_once_with(7)
    publication_dao.delete.assert_called_once_with(publication)


def test_delete_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Publication not found"):
        service.delete_publication(99)

    publication_dao.delete.assert_not_called()


@pytest.mark.parametrize("operation", ["get_by_id", "delete"])
def test_delete_database_unavailable_raises_service_unavailable(
    service: PublicationService, publication_dao: MagicMock, operation: str
) -> None:
    publication = Publication(publication_id=7, title="A Study of Things")
    publication_dao.get_by_id.return_value = publication
    getattr(publication_dao, operation).side_effect = OperationalError(
        "DELETE FROM publication", {}, Exception("database unavailable")
    )

    with pytest.raises(ServiceUnavailableError, match="Database unavailable"):
        service.delete_publication(7)
