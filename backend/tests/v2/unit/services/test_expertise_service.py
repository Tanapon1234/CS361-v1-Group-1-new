from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, NotFoundError
from app.v2.daos.expertise_dao import ExpertiseDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.dtos.expertise_dto import (
    ExpertiseCreateRequest,
    ExpertiseListQuery,
    ExpertiseUpdateRequest,
    LecturerExpertiseReplaceRequest,
)
from app.v2.models.expertise import Expertise
from app.v2.models.lecturer import Lecturer
from app.v2.services.expertise_service import ExpertiseService

LECTURER_ID = uuid4()


@pytest.fixture
def expertise_dao() -> MagicMock:
    dao = create_autospec(ExpertiseDAO, instance=True)
    dao.get_by_description.return_value = None
    return dao


@pytest.fixture
def lecturer_dao() -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.return_value = Lecturer(
        lecturer_id=LECTURER_ID, name_th="สมชาย", email="somchai@example.ac.th"
    )
    return dao


@pytest.fixture
def service(expertise_dao: MagicMock, lecturer_dao: MagicMock) -> ExpertiseService:
    return ExpertiseService(expertise_dao, lecturer_dao)


def test_get_unknown_expertise_raises_not_found(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    expertise_dao.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_expertise(99)


def test_list_returns_a_page(service: ExpertiseService, expertise_dao: MagicMock) -> None:
    expertise_dao.find_page.return_value = ([Expertise(expertise_id=1, description="AI")], 1)

    result = service.list_expertise(ExpertiseListQuery(q="ai", limit=10, offset=0))

    expertise_dao.find_page.assert_called_once_with(q="ai", limit=10, offset=0)
    assert result.meta.total == 1


def test_create_duplicate_raises_conflict(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    expertise_dao.get_by_description.return_value = Expertise(expertise_id=1, description="AI")

    with pytest.raises(ConflictError):
        service.create_expertise(ExpertiseCreateRequest(description="ai"))
    expertise_dao.add.assert_not_called()


def test_rename_to_its_own_name_is_allowed(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    row = Expertise(expertise_id=1, description="AI")
    expertise_dao.get_by_id.return_value = row
    expertise_dao.get_by_description.return_value = row
    expertise_dao.update.return_value = row

    service.update_expertise(1, ExpertiseUpdateRequest(description="AI"))

    expertise_dao.update.assert_called_once_with(row, {"description": "AI"})


def test_replace_with_unknown_id_changes_nothing(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    expertise_dao.get_by_id.side_effect = lambda i: (
        Expertise(expertise_id=1, description="AI") if i == 1 else None
    )

    with pytest.raises(NotFoundError):
        service.replace_lecturer_expertise(
            LECTURER_ID, LecturerExpertiseReplaceRequest(expertise_ids=[1, 2])
        )
    expertise_dao.replace_for_lecturer.assert_not_called()


def test_replace_returns_the_new_set(service: ExpertiseService, expertise_dao: MagicMock) -> None:
    expertise_dao.get_by_id.return_value = Expertise(expertise_id=1, description="AI")
    expertise_dao.list_by_lecturer.return_value = [Expertise(expertise_id=1, description="AI")]

    result = service.replace_lecturer_expertise(
        LECTURER_ID, LecturerExpertiseReplaceRequest(expertise_ids=[1])
    )

    expertise_dao.replace_for_lecturer.assert_called_once_with(LECTURER_ID, [1])
    assert [item.expertise_id for item in result.items] == [1]


def test_remove_not_assigned_is_not_found(
    service: ExpertiseService, expertise_dao: MagicMock
) -> None:
    expertise_dao.get_by_id.return_value = Expertise(expertise_id=1, description="AI")
    expertise_dao.remove_from_lecturer.return_value = False

    with pytest.raises(NotFoundError):
        service.remove_lecturer_expertise(LECTURER_ID, 1)


def test_replace_rejects_duplicate_ids() -> None:
    with pytest.raises(ValidationError):
        LecturerExpertiseReplaceRequest(expertise_ids=[1, 1])
