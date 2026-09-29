from unittest.mock import MagicMock, create_autospec

import pytest

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


def test_list_research_interests_returns_page(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = (
        [ResearchInterest(research_interest_id=1, name="Machine Learning")],
        1,
    )

    result = service.list_research_interests(ResearchInterestListQuery(search="Machine"))

    assert result.data[0].name == "Machine Learning"
    assert result.pagination.total == 1
    assert result.pagination.total_pages == 1
    research_interest_dao.find_page.assert_called_once_with(
        search="Machine", limit=20, offset=0, sort_order="asc"
    )


def test_list_research_interests_paginates(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = (
        [ResearchInterest(research_interest_id=11, name="Robotics")],
        21,
    )

    result = service.list_research_interests(
        ResearchInterestListQuery(page=2, limit=10, sort_order="desc")
    )

    assert result.pagination.page == 2
    assert result.pagination.limit == 10
    assert result.pagination.total == 21
    assert result.pagination.total_pages == 3
    research_interest_dao.find_page.assert_called_once_with(
        search=None, limit=10, offset=10, sort_order="desc"
    )


def test_list_research_interests_empty_result(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = ([], 0)

    result = service.list_research_interests(ResearchInterestListQuery())

    assert result.data == []
    assert result.pagination.total == 0
    assert result.pagination.total_pages == 0


@pytest.mark.xfail(raises=NotImplementedError, reason="TODO: implement update")
def test_update_unknown_research_interest_raises_not_found(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_research_interest(99, ResearchInterestUpdateRequest(name="x"))
