"""See test_lecturer_service.py for how these xfail tests work."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.publication_dto import PublicationUpdateRequest
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


def publication(**overrides: object) -> Publication:
    values: dict[str, object] = {
        "publication_id": 1,
        "title": "A New Mobile Application",
        "publication_year": 2018,
        "venue": "Hospital Pediatrics",
        "volume": "8",
        "pages": None,
        "doi": "10.1542/hpeds.2018-0073",
        "citation_text": "Wantanakorn, Pornchanok & ...",
        "created_at": datetime(2026, 10, 1, tzinfo=UTC),
    }
    return Publication(**(values | overrides))


def test_update_publication_single_field(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    existing = publication()
    updated = publication(volume="9")
    publication_dao.get_by_id.return_value = existing
    publication_dao.update.return_value = updated

    result = service.update_publication(1, PublicationUpdateRequest(volume="9"))

    publication_dao.update.assert_called_once_with(existing, {"volume": "9"})
    publication_dao.get_by_doi.assert_not_called()
    assert result.volume == "9"
    assert result.title == existing.title


def test_update_publication_multiple_fields_only_updates_sent_fields(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    existing = publication()
    updated = publication(volume="9", pages="100-110")
    publication_dao.get_by_id.return_value = existing
    publication_dao.update.return_value = updated

    result = service.update_publication(
        1,
        PublicationUpdateRequest(volume="9", pages="100-110"),
    )

    publication_dao.update.assert_called_once_with(
        existing,
        {"volume": "9", "pages": "100-110"},
    )
    assert result.volume == "9"
    assert result.pages == "100-110"
    assert result.venue == "Hospital Pediatrics"


def test_update_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Publication not found"):
        service.update_publication(99, PublicationUpdateRequest(volume="9"))

    publication_dao.update.assert_not_called()


def test_update_publication_duplicate_doi_raises_conflict(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    existing = publication()
    publication_dao.get_by_id.return_value = existing
    publication_dao.get_by_doi.return_value = publication(
        publication_id=2,
        title="Another publication",
        doi="10.1000/duplicate",
    )

    with pytest.raises(ConflictError, match="Publication DOI already exists"):
        service.update_publication(
            1,
            PublicationUpdateRequest(doi="10.1000/duplicate"),
        )

    publication_dao.update.assert_not_called()


def test_update_publication_allows_same_record_doi(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    existing = publication()
    publication_dao.get_by_id.return_value = existing
    publication_dao.get_by_doi.return_value = existing
    publication_dao.update.return_value = existing

    service.update_publication(
        1,
        PublicationUpdateRequest(doi="10.1542/hpeds.2018-0073"),
    )

    publication_dao.update.assert_called_once_with(
        existing,
        {"doi": "10.1542/hpeds.2018-0073"},
    )


def test_update_publication_unique_violation_raises_conflict(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = publication()
    publication_dao.get_by_doi.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    publication_dao.update.side_effect = IntegrityError("UPDATE publication", {}, unique_violation)

    with pytest.raises(ConflictError, match="Publication DOI already exists"):
        service.update_publication(
            1,
            PublicationUpdateRequest(doi="10.1000/concurrent"),
        )


def test_update_publication_database_unavailable(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.side_effect = OperationalError(
        "SELECT publication", {}, Exception("connection refused")
    )

    with pytest.raises(ServiceUnavailableError, match="Database is unreachable"):
        service.update_publication(1, PublicationUpdateRequest(volume="9"))


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement get publication")
def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_publication(99)
