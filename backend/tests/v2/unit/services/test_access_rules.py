"""Checks of docs/v2/permissions.md that depend on data (app/v2/services/access.py and the
services that use it). Route-level rules are in tests/v2/test_permissions.py."""

from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError
from app.v2.daos.department_dao import DepartmentDAO
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.publication_dao import PublicationDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.lecturer_dto import LecturerUpdateRequest
from app.v2.dtos.publication_dto import PublicationCreateRequest, PublicationUpdateRequest
from app.v2.dtos.submission_dto import SubmissionListQuery
from app.v2.models.enums import AcademicRank, PositionCode
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import Publication
from app.v2.models.submission import Submission
from app.v2.security import Actor, HeldPosition, Role
from app.v2.services.access import can_view_submission, require_department_view
from app.v2.services.lecturer_service import LecturerService
from app.v2.services.publication_service import PublicationService
from app.v2.services.score_keeper import ScoreKeeper
from app.v2.services.submission_service import SubmissionService
from app.v2.storage.object_storage import ObjectStorage

OWNER = uuid4()
SUBMISSION = Submission(
    id=uuid4(),
    round_id=1,
    lecturer_id=OWNER,
    rank_snapshot=AcademicRank.LECTURER,
    department_snapshot=7,
)


def lecturer(lecturer_id=None, *roles: Role, positions=()) -> Actor:
    return Actor(
        lecturer_id or uuid4(),
        frozenset({Role.LECTURER, *roles}),
        frozenset(HeldPosition(p, d) for p, d in positions),
    )


@pytest.mark.parametrize(
    ("actor", "allowed"),
    [
        (lecturer(OWNER), True),
        (lecturer(), False),
        (lecturer(None, Role.EXECUTIVE), True),
        (lecturer(None, Role.REVIEWER), True),
        (lecturer(positions=[(PositionCode.DEPT_CHAIR, 7)]), True),
        (lecturer(positions=[(PositionCode.DEPT_COMMITTEE, 8)]), False),
        (lecturer(positions=[(PositionCode.EXEC_COMMITTEE, None)]), False),
    ],
    ids=[
        "owner",
        "other-lecturer",
        "executive",
        "reviewer",
        "chair-same-dept",
        "committee-other-dept",
        "exec-committee-position-only",
    ],
)
def test_who_sees_a_submission(actor: Actor, allowed: bool) -> None:
    assert can_view_submission(actor, SUBMISSION) is allowed


def test_department_lists_are_narrowed_for_department_signers() -> None:
    chair = lecturer(positions=[(PositionCode.DEPT_CHAIR, 7)])

    assert require_department_view(chair, None) == 7
    assert require_department_view(chair, 7) == 7
    with pytest.raises(ForbiddenError):
        require_department_view(chair, 8)
    assert require_department_view(lecturer(None, Role.STAFF), None) is None


# --- submissions list ---------------------------------------------------------------


@pytest.fixture
def submission_dao() -> MagicMock:
    dao = create_autospec(SubmissionDAO, instance=True)
    dao.find_page.return_value = ([], 0)
    return dao


@pytest.fixture
def submissions(submission_dao: MagicMock) -> SubmissionService:
    return SubmissionService(
        submission_dao,
        create_autospec(EvaluationRoundDAO, instance=True),
        create_autospec(LecturerDAO, instance=True),
        create_autospec(EvidenceDAO, instance=True),
        create_autospec(ObjectStorage, instance=True),
        create_autospec(ScoreKeeper, instance=True),
    )


@pytest.mark.parametrize(
    ("actor", "expected"),
    [
        (lecturer(OWNER), {"lecturer_id": OWNER, "department_id": None}),
        (
            lecturer(positions=[(PositionCode.DEPT_CHAIR, 7)]),
            {"lecturer_id": None, "department_id": 7},
        ),
        (lecturer(None, Role.STAFF), {"lecturer_id": None, "department_id": None}),
    ],
    ids=["lecturer-sees-own", "chair-sees-department", "staff-sees-all"],
)
def test_submission_list_is_scoped_to_the_caller(
    submissions: SubmissionService, submission_dao: MagicMock, actor: Actor, expected: dict
) -> None:
    submissions.list_submissions(actor, SubmissionListQuery())

    called = submission_dao.find_page.call_args.kwargs
    assert {key: called[key] for key in expected} == expected


def test_lecturer_cannot_list_someone_elses_submissions(
    submissions: SubmissionService, submission_dao: MagicMock
) -> None:
    me = lecturer(OWNER)

    submissions.list_submissions(me, SubmissionListQuery(lecturer_id=uuid4()))

    assert submission_dao.find_page.call_args.kwargs["lecturer_id"] == OWNER


# --- lecturer self edit ---------------------------------------------------------------


@pytest.fixture
def lecturer_dao() -> MagicMock:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.return_value = Lecturer(lecturer_id=OWNER, name_th="ก", email="a@x.th")
    dao.update.side_effect = lambda row, values: row.sqlmodel_update(values) or row
    return dao


@pytest.fixture
def lecturers(lecturer_dao: MagicMock) -> LecturerService:
    return LecturerService(lecturer_dao, create_autospec(DepartmentDAO, instance=True))


def test_lecturer_may_change_their_contact_details(lecturers: LecturerService) -> None:
    result = lecturers.update_lecturer(
        OWNER, LecturerUpdateRequest(office="SC-1", phone="02"), actor=lecturer(OWNER)
    )

    assert result.office == "SC-1"


@pytest.mark.parametrize(
    "body",
    [{"email": "b@x.th"}, {"department_id": 2}, {"rank": "ศาสตราจารย์"}, {"cognito_sub": "x"}],
    ids=["email", "department", "rank", "account"],
)
def test_only_staff_change_identity_and_position_fields(
    lecturers: LecturerService, lecturer_dao: MagicMock, body: dict
) -> None:
    with pytest.raises(ForbiddenError, match="Only staff"):
        lecturers.update_lecturer(OWNER, LecturerUpdateRequest(**body), actor=lecturer(OWNER))
    lecturer_dao.update.assert_not_called()


# --- publications ---------------------------------------------------------------------


@pytest.fixture
def publication_dao() -> MagicMock:
    dao = create_autospec(PublicationDAO, instance=True)
    dao.get_by_id.return_value = Publication(publication_id=1, title="T")
    dao.get_author_ids.return_value = [OWNER]
    dao.get_by_doi.return_value = None
    return dao


@pytest.fixture
def publications(publication_dao: MagicMock) -> PublicationService:
    dao = create_autospec(LecturerDAO, instance=True)
    dao.get_by_id.side_effect = lambda lecturer_id: Lecturer(
        lecturer_id=lecturer_id, name_th="ก", email=f"{lecturer_id}@x.th"
    )
    return PublicationService(publication_dao, dao)


def test_lecturers_add_only_their_own_publications(
    publications: PublicationService, publication_dao: MagicMock
) -> None:
    with pytest.raises(ForbiddenError, match="yourself"):
        publications.create_publication(
            PublicationCreateRequest(title="T", lecturer_ids=[uuid4()]), actor=lecturer(OWNER)
        )
    publication_dao.add.assert_not_called()


@pytest.mark.parametrize(
    ("actor", "allowed"),
    [(lecturer(OWNER), True), (lecturer(), False), (lecturer(None, Role.STAFF), True)],
    ids=["author", "not-an-author", "staff"],
)
def test_authors_or_staff_change_a_publication(
    publications: PublicationService, publication_dao: MagicMock, actor: Actor, allowed: bool
) -> None:
    publication_dao.update.return_value = publication_dao.get_by_id.return_value

    if allowed:
        publications.update_publication(1, PublicationUpdateRequest(volume="2"), actor=actor)
        publications.delete_publication(1, actor=actor)
    else:
        with pytest.raises(ForbiddenError):
            publications.update_publication(1, PublicationUpdateRequest(volume="2"), actor=actor)
        with pytest.raises(ForbiddenError):
            publications.delete_publication(1, actor=actor)
        publication_dao.delete.assert_not_called()
