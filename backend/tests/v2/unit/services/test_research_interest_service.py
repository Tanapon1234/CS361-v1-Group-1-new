from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.research_interest_dao import ResearchInterestDAO
from app.v2.dtos.research_interest_dto import (
    LecturerResearchInterestListQuery,
    LecturerResearchInterestsReplaceRequest,
    ResearchInterestCreateRequest,
    ResearchInterestListQuery,
    ResearchInterestUpdateRequest,
)
from app.v2.models.lecturer import Lecturer
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
    assert result.meta.limit == 20
    assert result.meta.offset == 0
    research_interest_dao.find_page.assert_called_once_with(
        q="Machine", limit=20, offset=0
    )


def test_list_research_interests_paginates(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = (
        [ResearchInterest(research_interest_id=11, name="Robotics")],
        21,
    )

    result = service.list_research_interests(
        ResearchInterestListQuery(limit=10, offset=10)
    )

    assert result.meta.limit == 10
    assert result.meta.offset == 10
    assert result.meta.total == 21
    research_interest_dao.find_page.assert_called_once_with(
        q=None, limit=10, offset=10
    )


def test_list_research_interests_empty_result(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.find_page.return_value = ([], 0)

    result = service.list_research_interests(ResearchInterestListQuery())

    assert result.items == []
    assert result.meta.total == 0


def test_list_lecturer_research_interests_for_existing_lecturer(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )
    research_interest_dao.list_by_lecturer.return_value = [
        ResearchInterest(research_interest_id=1, name="Machine Learning"),
        ResearchInterest(research_interest_id=2, name="Machine Learning in Healthcare"),
    ]

    result = service.list_lecturer_research_interests(lecturer_id)

    assert [item.name for item in result.items] == [
        "Machine Learning",
        "Machine Learning in Healthcare",
    ]
    assert result.meta.count == 2
    lecturer_dao.get_by_id.assert_called_once_with(lecturer_id)
    research_interest_dao.list_by_lecturer.assert_called_once_with(lecturer_id)


def test_list_lecturer_research_interests_empty(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )
    research_interest_dao.list_by_lecturer.return_value = []

    result = service.list_lecturer_research_interests(lecturer_id)

    assert result.items == []
    assert result.meta.count == 0
    research_interest_dao.list_by_lecturer.assert_called_once_with(lecturer_id)


def test_list_lecturer_research_interests_unknown_lecturer_raises_not_found(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.list_lecturer_research_interests(lecturer_id, LecturerResearchInterestListQuery())

    research_interest_dao.list_by_lecturer.assert_not_called()


def test_replace_lecturer_research_interests_replaces_complete_set(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )
    interests = {
        1: ResearchInterest(research_interest_id=1, name="Machine Learning"),
        3: ResearchInterest(research_interest_id=3, name="Computer Vision"),
    }
    research_interest_dao.get_by_id.side_effect = interests.get

    result = service.replace_lecturer_research_interests(
        lecturer_id,
        LecturerResearchInterestsReplaceRequest(research_interest_ids=[1, 3]),
    )

    research_interest_dao.replace_for_lecturer.assert_called_once_with(lecturer_id, [1, 3])
    assert [item.research_interest_id for item in result.items] == [1, 3]
    assert result.meta.count == 2


def test_replace_lecturer_research_interests_empty_list_clears_all(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )

    result = service.replace_lecturer_research_interests(
        lecturer_id,
        LecturerResearchInterestsReplaceRequest(research_interest_ids=[]),
    )

    research_interest_dao.get_by_id.assert_not_called()
    research_interest_dao.replace_for_lecturer.assert_called_once_with(lecturer_id, [])
    assert result.items == []
    assert result.meta.count == 0


def test_replace_lecturer_research_interests_unknown_lecturer_does_not_write(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError, match="Lecturer not found"):
        service.replace_lecturer_research_interests(
            lecturer_id,
            LecturerResearchInterestsReplaceRequest(research_interest_ids=[1]),
        )

    research_interest_dao.get_by_id.assert_not_called()
    research_interest_dao.replace_for_lecturer.assert_not_called()


def test_replace_lecturer_research_interests_unknown_interest_does_not_write(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )
    research_interest_dao.get_by_id.side_effect = [
        ResearchInterest(research_interest_id=1, name="Machine Learning"),
        None,
    ]

    with pytest.raises(NotFoundError, match="Research interest 99 not found"):
        service.replace_lecturer_research_interests(
            lecturer_id,
            LecturerResearchInterestsReplaceRequest(research_interest_ids=[1, 99]),
        )

    research_interest_dao.replace_for_lecturer.assert_not_called()


def test_replace_lecturer_research_interests_propagates_write_error_for_rollback(
    service: ResearchInterestService, research_interest_dao: MagicMock, lecturer_dao: MagicMock
) -> None:
    lecturer_id = uuid4()
    lecturer_dao.get_by_id.return_value = Lecturer(
        lecturer_id=lecturer_id, name_th="Somchai", email="somchai@example.ac.th"
    )
    research_interest_dao.get_by_id.return_value = ResearchInterest(
        research_interest_id=1, name="Machine Learning"
    )
    research_interest_dao.replace_for_lecturer.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        service.replace_lecturer_research_interests(
            lecturer_id,
            LecturerResearchInterestsReplaceRequest(research_interest_ids=[1]),
        )


def test_update_research_interest_success(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    existing = ResearchInterest(research_interest_id=1, name="Machine Learning")
    updated = ResearchInterest(research_interest_id=1, name="Deep Learning")
    research_interest_dao.get_by_id.return_value = existing
    research_interest_dao.get_by_name.return_value = None
    research_interest_dao.update.return_value = updated

    result = service.update_research_interest(
        1, ResearchInterestUpdateRequest(name="Deep Learning")
    )

    assert result.research_interest_id == 1
    assert result.name == "Deep Learning"
    research_interest_dao.update.assert_called_once_with(existing, {"name": "Deep Learning"})


def test_update_unknown_research_interest_raises_not_found(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.update_research_interest(99, ResearchInterestUpdateRequest(name="x"))

    research_interest_dao.update.assert_not_called()


def test_update_research_interest_duplicate_name_raises_conflict(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    research_interest_dao.get_by_id.return_value = ResearchInterest(
        research_interest_id=1, name="Machine Learning"
    )
    research_interest_dao.get_by_name.return_value = ResearchInterest(
        research_interest_id=2, name="Deep Learning"
    )

    with pytest.raises(ConflictError):
        service.update_research_interest(1, ResearchInterestUpdateRequest(name="Deep Learning"))

    research_interest_dao.update.assert_not_called()


def test_update_research_interest_allows_same_record_name(
    service: ResearchInterestService, research_interest_dao: MagicMock
) -> None:
    existing = ResearchInterest(research_interest_id=1, name="Machine Learning")
    research_interest_dao.get_by_id.return_value = existing
    research_interest_dao.get_by_name.return_value = existing
    research_interest_dao.update.return_value = existing

    result = service.update_research_interest(
        1, ResearchInterestUpdateRequest(name="Machine Learning")
    )

    assert result.research_interest_id == 1
    assert result.name == "Machine Learning"
