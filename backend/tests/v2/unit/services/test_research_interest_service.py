from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.research_interest_dto import (
    ResearchInterestCreateRequest,
    ResearchInterestListQuery,
    ResearchInterestUpdateRequest,
)
from app.v2.models.research_interest import ResearchInterest
from app.v2.services.research_interest_service import ResearchInterestService


@pytest.fixture
def research_interest_dao() -> MagicMock:
    return create_autospec(ResearchInterestDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(research_interest_dao: MagicMock, lecturer_dao: MagicMock) -> ResearchInterestService:
    return ResearchInterestService(research_interest_dao, lecturer_dao)


def test_create_research_interest_with_valid_name(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_name.return_value = None
    research_interest_dao.add.return_value = ResearchInterest(
        research_interest_id=1, name="Machine Learning"
    )

    result = service.create_research_interest(
        ResearchInterestCreateRequest(name="Machine Learning")
    )

    assert result.research_interest_id == 1
    assert result.name == "Machine Learning"
    added = research_interest_dao.add.call_args.args[0]
    assert added.name == "Machine Learning"


def test_create_research_interest_duplicate_name_raises_conflict(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_name.return_value = ResearchInterest(
        research_interest_id=1, name="Machine Learning"
    )

    with pytest.raises(ConflictError):
        service.create_research_interest(ResearchInterestCreateRequest(name="Machine Learning"))

    research_interest_dao.add.assert_not_called()


def test_create_research_interest_integrity_error_raises_conflict(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_name.return_value = None
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    research_interest_dao.add.side_effect = IntegrityError(
        "INSERT INTO research_interest", {}, unique_violation
    )

    with pytest.raises(ConflictError, match="Research interest name already exists"):
        service.create_research_interest(ResearchInterestCreateRequest(name="Machine Learning"))


def test_create_research_interest_propagates_unexpected_error_for_rollback(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_name.return_value = None
    research_interest_dao.add.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.create_research_interest(ResearchInterestCreateRequest(name="Machine Learning"))


def test_list_research_interests_returns_page(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = (
        [ResearchInterest(research_interest_id=1, name="Machine Learning")],
        1,
    )

    result = service.list_research_interests(ResearchInterestListQuery(q="Machine"))

    assert result.items[0].name == "Machine Learning"
    assert result.meta.total == 1
    research_interest_dao.find_page.assert_called_once_with(q="Machine", limit=20, offset=0)


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement update")
def test_update_unknown_research_interest_raises_not_found(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_research_interest(99, ResearchInterestUpdateRequest(name="x"))
