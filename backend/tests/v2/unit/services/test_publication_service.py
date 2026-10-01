"""See test_lecturer_service.py for how these xfail tests work."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.publication_dto import PublicationListQuery
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


def test_list_publications_returns_page_and_maps_models(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    publication_dao.find_page.return_value = (
        [
            Publication(
                publication_id=1,
                title="A New Mobile Application",
                publication_year=2018,
                venue="Hospital Pediatrics",
                volume="8",
                pages=None,
                doi="10.1542/hpeds.2018-0073",
                citation_text="Wantanakorn, Pornchanok & ...",
                created_at=created_at,
            )
        ],
        1,
    )
    query = PublicationListQuery(q="mobile", publication_year=2018, limit=10, offset=20)

    result = service.list_publications(query)

    publication_dao.find_page.assert_called_once_with(
        q="mobile",
        publication_year=2018,
        lecturer_id=None,
        limit=10,
        offset=20,
    )
    assert result.meta.total == 1
    assert result.meta.limit == 10
    assert result.meta.offset == 20
    assert result.items[0].publication_id == 1
    assert result.items[0].pages is None
    assert result.items[0].created_at == created_at


def test_list_publications_empty_result(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.find_page.return_value = ([], 0)

    result = service.list_publications(PublicationListQuery())

    assert result.items == []
    assert result.meta.total == 0
    publication_dao.find_page.assert_called_once_with(
        q=None,
        publication_year=None,
        lecturer_id=None,
        limit=20,
        offset=0,
    )


def test_list_publications_database_unavailable(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.find_page.side_effect = OperationalError(
        "SELECT publication", {}, Exception("connection refused")
    )

    with pytest.raises(ServiceUnavailableError, match="Database is unreachable"):
        service.list_publications(PublicationListQuery())


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement get publication")
def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_publication(99)
