"""See test_lecturer_service.py for how these xfail tests work."""

from unittest.mock import MagicMock, create_autospec

import pytest

from app.core.exceptions import NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.research_interest_dto import ResearchInterestUpdateRequest
from app.v2.services.research_interest_service import ResearchInterestService

pytestmark = pytest.mark.xfail(
    raises=NotImplementedError, reason="TODO: implement ResearchInterestService"
)


@pytest.fixture
def research_interest_dao() -> MagicMock:
    return create_autospec(ResearchInterestDAO, instance=True)


@pytest.fixture
def lecturer_dao() -> MagicMock:
    return create_autospec(LecturerDAO, instance=True)


@pytest.fixture
def service(research_interest_dao: MagicMock, lecturer_dao: MagicMock) -> ResearchInterestService:
    return ResearchInterestService(research_interest_dao, lecturer_dao)


def test_update_unknown_research_interest_raises_not_found(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_research_interest(99, ResearchInterestUpdateRequest(name="x"))
