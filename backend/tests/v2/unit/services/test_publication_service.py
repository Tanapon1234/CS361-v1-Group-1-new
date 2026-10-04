"""See test_lecturer_service.py for how these xfail tests work."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.dtos.publication_dto import (
    PublicationCreateRequest,
    PublicationListQuery,
    PublicationUpdateRequest,
)
from app.v2.models.lecturer import Lecturer
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

    publication_dao.update.assert_not_called()


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


def test_get_publication_returns_mapped_dto(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    created_at = datetime(2026, 10, 1, tzinfo=UTC)
    publication_dao.get_by_id.return_value = Publication(
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

    result = service.get_publication(1)

    publication_dao.get_by_id.assert_called_once_with(1)
    assert result.publication_id == 1
    assert result.title == "A New Mobile Application"
    assert result.pages is None
    assert result.created_at == created_at


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


def test_get_unknown_publication_raises_not_found(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Publication not found"):
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


def test_get_publication_database_unavailable(
    service: PublicationService, publication_dao: MagicMock
) -> None:
    publication_dao.get_by_id.side_effect = OperationalError(
        "SELECT publication", {}, Exception("connection refused")
    )

    with pytest.raises(ServiceUnavailableError, match="Database is unreachable"):
        service.get_publication(1)


def test_list_lecturer_publications_returns_page_with_author_order(
    service: PublicationService,
    publication_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="Somchai",
        email="somchai@example.ac.th",
    )
    publication_dao.find_lecturer_page.return_value = (
        [
            (
                Publication(
                    publication_id=1,
                    title="A New Mobile Application",
                    publication_year=2018,
                    venue="Hospital Pediatrics",
                    doi="10.1542/hpeds.2018-0073",
                ),
                5,
            )
        ],
        1,
    )
    query = PublicationListQuery(q="mobile", publication_year=2018, limit=10, offset=20)

    result = service.list_lecturer_publications(lecturer_id, query)

    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)
    publication_dao.find_lecturer_page.assert_called_once_with(
        lecturer_id,
        q="mobile",
        publication_year=2018,
        limit=10,
        offset=20,
    )
    assert result.items[0].publication_id == 1
    assert result.items[0].author_order == 5
    assert result.meta.total == 1
    assert result.meta.limit == 10
    assert result.meta.offset == 20


def test_list_lecturer_publications_empty(
    service: PublicationService,
    publication_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id,
        name_th="Somchai",
        email="somchai@example.ac.th",
    )
    publication_dao.find_lecturer_page.return_value = ([], 0)

    result = service.list_lecturer_publications(lecturer_id, PublicationListQuery())

    assert result.items == []
    assert result.meta.total == 0


def test_list_lecturer_publications_unknown_lecturer_does_not_query_publications(
    service: PublicationService,
    publication_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.list_lecturer_publications(lecturer_id, PublicationListQuery())

    publication_dao.find_lecturer_page.assert_not_called()


def test_list_lecturer_publications_database_unavailable(
    service: PublicationService,
    publication_dao: MagicMock,
    lecturer_dao: MagicMock,
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.side_effect = OperationalError(
        "SELECT lecturer", {}, Exception("connection refused")
    )

    with pytest.raises(ServiceUnavailableError, match="Database is unreachable"):
        service.list_lecturer_publications(lecturer_id, PublicationListQuery())
