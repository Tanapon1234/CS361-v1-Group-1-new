"""ReviewerAssignmentService rules with mocked DAOs (V4 #293)."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.v2.models.lecturer import Lecturer
from app.v2.models.reviewer_assignment import ReviewerAssignment
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.dtos.reviewer_assignment_dto import (
    ReviewerAssignmentCreateRequest,
    ReviewerAssignmentListQuery,
)
from app.v3.security import Actor, Role
from app.v3.services.reviewer_assignment_service import ReviewerAssignmentService

EXECUTIVE = Actor(uuid4(), frozenset({Role.LECTURER, Role.EXECUTIVE}))
REVIEWER = Actor(uuid4(), frozenset({Role.LECTURER, Role.REVIEWER}))
PLAIN_LECTURER = Actor(uuid4(), frozenset({Role.LECTURER}))


def lecturer(lecturer_id) -> Lecturer:
    return Lecturer(lecturer_id=lecturer_id, name_th="ก", email=f"{lecturer_id}@x.th")


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    assignment_dao = create_autospec(ReviewerAssignmentDAO, instance=True)
    lecturer_dao = create_autospec(LecturerDAO, instance=True)
    lecturer_dao.get_by_id.side_effect = lambda lecturer_id: lecturer(lecturer_id)
    return {"assignment": assignment_dao, "lecturer": lecturer_dao}


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> ReviewerAssignmentService:
    return ReviewerAssignmentService(daos["assignment"], daos["lecturer"])


def test_executive_assigns_a_reviewer(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    reviewer_id, reviewee_id = uuid4(), uuid4()
    daos["assignment"].add.side_effect = lambda a: a

    result = service.create_assignment(
        EXECUTIVE, ReviewerAssignmentCreateRequest(reviewer_id=reviewer_id, reviewee_id=reviewee_id)
    )

    assert result.reviewer_id == reviewer_id
    assert result.reviewee_id == reviewee_id
    assert result.assigned_by == EXECUTIVE.lecturer_id


def test_duplicate_assignment_is_a_conflict(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    unique_violation = Exception("duplicate")
    unique_violation.sqlstate = "23505"  # type: ignore[attr-defined]
    daos["assignment"].add.side_effect = IntegrityError("INSERT", {}, unique_violation)

    with pytest.raises(ConflictError):
        service.create_assignment(
            EXECUTIVE,
            ReviewerAssignmentCreateRequest(reviewer_id=uuid4(), reviewee_id=uuid4()),
        )


def test_assigning_an_unknown_lecturer_is_not_found(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    daos["lecturer"].get_by_id.side_effect = None
    daos["lecturer"].get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.create_assignment(
            EXECUTIVE,
            ReviewerAssignmentCreateRequest(reviewer_id=uuid4(), reviewee_id=uuid4()),
        )


def test_reviewer_id_and_reviewee_id_must_differ() -> None:
    same = uuid4()
    with pytest.raises(ValueError, match="must not be the same"):
        ReviewerAssignmentCreateRequest(reviewer_id=same, reviewee_id=same)


def test_executive_lists_any_assignment(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    row = ReviewerAssignment(reviewer_id=uuid4(), reviewee_id=uuid4(), assigned_by=uuid4())
    daos["assignment"].list_all.return_value = [row]

    result = service.list_assignments(EXECUTIVE, ReviewerAssignmentListQuery())

    assert result.meta.count == 1
    daos["assignment"].list_all.assert_called_once_with(reviewer_id=None, reviewee_id=None)


def test_reviewer_only_lists_their_own_assignments(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    daos["assignment"].list_by_reviewer.return_value = []

    service.list_assignments(REVIEWER, ReviewerAssignmentListQuery(reviewee_id=uuid4()))

    daos["assignment"].list_by_reviewer.assert_called_once_with(REVIEWER.lecturer_id)
    daos["assignment"].list_all.assert_not_called()


def test_a_plain_lecturer_may_not_list_assignments(
    service: ReviewerAssignmentService,
) -> None:
    with pytest.raises(ForbiddenError):
        service.list_assignments(PLAIN_LECTURER, ReviewerAssignmentListQuery())


def test_delete_an_unknown_assignment_is_not_found(
    service: ReviewerAssignmentService, daos: dict[str, MagicMock]
) -> None:
    daos["assignment"].get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.delete_assignment(uuid4())
