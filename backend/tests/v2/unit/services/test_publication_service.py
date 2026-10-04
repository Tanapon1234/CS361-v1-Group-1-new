"""See test_lecturer_service.py for how these xfail tests work."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.publication_dto import PublicationCreateRequest
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


def test_create_publication_success(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    publication_dao.get_by_doi.return_value = None
    publication_dao.add.return_value = Publication(
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
    data = PublicationCreateRequest(
        title="A New Mobile Application",
        publication_year=2018,
        venue="Hospital Pediatrics",
        volume="8",
        pages=None,
        doi="10.1542/hpeds.2018-0073",
        citation_text="Wantanakorn, Pornchanok & ...",
    )

    result = service.create_publication(data)

    assert result.publication_id == 1
    assert result.created_at == created_at
    assert result.pages is None
    publication_dao.get_by_doi.assert_called_once_with("10.1542/hpeds.2018-0073")
    added = publication_dao.add.call_args.args[0]
    assert added.title == data.title
    assert added.publication_year == data.publication_year
    assert added.pages is None


def test_create_publication_accepts_null_optional_fields(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.add.return_value = Publication(
        publication_id=1,
        title="Publication without metadata",
    )

    result = service.create_publication(
        PublicationCreateRequest(title="Publication without metadata")
    )

    assert result.publication_year is None
    assert result.venue is None
    assert result.volume is None
    assert result.pages is None
    assert result.doi is None
    publication_dao.get_by_doi.assert_not_called()


def test_create_publication_duplicate_doi_raises_conflict(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_doi.return_value = Publication(
        publication_id=1,
        title="Existing publication",
        doi="10.1542/hpeds.2018-0073",
    )

    with pytest.raises(ConflictError, match="Publication DOI already exists"):
        service.create_publication(
            PublicationCreateRequest(
                title="Duplicate publication",
                doi="10.1542/hpeds.2018-0073",
            )
        )

    publication_dao.add.assert_not_called()


def test_create_publication_unique_violation_raises_conflict(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_doi.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    publication_dao.add.side_effect = IntegrityError("INSERT publication", {}, unique_violation)

    with pytest.raises(ConflictError, match="Publication DOI already exists"):
        service.create_publication(
            PublicationCreateRequest(
                title="Concurrent duplicate",
                doi="10.1542/hpeds.2018-0073",
            )
        )


def test_create_publication_dao_error_propagates_for_rollback(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.add.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.create_publication(PublicationCreateRequest(title="Failed publication"))


def test_create_publication_database_unavailable_raises_service_unavailable(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_doi.side_effect = OperationalError(
        "SELECT publication", {}, Exception("connection refused")
    )

    with pytest.raises(ServiceUnavailableError, match="Database is unreachable"):
        service.create_publication(
            PublicationCreateRequest(
                title="Unavailable publication",
                doi="10.1542/hpeds.2018-0073",
            )
        )

    publication_dao.add.assert_not_called()


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement get publication")
def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_publication(99)
