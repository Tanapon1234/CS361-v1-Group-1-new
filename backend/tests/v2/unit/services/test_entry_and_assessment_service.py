"""Entry and assessment rules with mocked DAOs."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.v2.daos.assessment_dao import AssessmentDAO
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.member_position_dao import MemberPositionDAO
from app.v2.daos.rubric_dao import RubricDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.assessment_dto import AssessmentPutRequest
from app.v2.dtos.submission_dto import EntryCreateRequest
from app.v2.models.enums import (
    AcademicRank,
    AssessmentAgg,
    PositionCode,
    QuantityUnit,
    RangeBasis,
    SubmissionStatus,
    WeightMode,
)
from app.v2.models.lecturer import Lecturer
from app.v2.models.member_position import MemberPosition
from app.v2.models.rubric import RubricItem, RubricSection, RubricVersion
from app.v2.models.submission import EntryAssessment, Submission, SubmissionEntry
from app.v2.services.assessment_service import AssessmentService
from app.v2.services.entry_service import EntryService
from app.v2.services.score_keeper import Rubric, ScoreKeeper
from app.v2.services.scoring import EntryScore
from app.v2.storage.object_storage import ObjectStorage

ACTOR = Lecturer(name_th="ผู้ใช้", email="u@x.th")
FIXED = RubricItem(id=1, section_id=1, label_th="x", weight=Decimal(1), unit=QuantityUnit.TOPIC)
RANGED = RubricItem(
    id=2,
    section_id=1,
    label_th="หัวหน้าสาขา",
    weight_mode=WeightMode.RANGED,
    weight_min=Decimal(1),
    weight_max=Decimal(2),
    range_basis=RangeBasis.WEIGHT,
    assessor_position=PositionCode.EXEC_COMMITTEE,
    assessment_agg=AssessmentAgg.SINGLE,
    unit=QuantityUnit.TERM,
)
SECTION = RubricSection(id=1, category_id=1, code="1.4", name_th="x", max_entries=2, sort_order=1)
RUBRIC = Rubric(
    version=RubricVersion(id=1, code="v1"),
    categories=[],
    sections=[SECTION],
    items={1: FIXED, 2: RANGED},
)


def submission(status: SubmissionStatus, owner: Lecturer | None = None) -> Submission:
    return Submission(
        round_id=1,
        lecturer_id=(owner or Lecturer(name_th="เจ้าของ", email="o@x.th")).lecturer_id,
        status=status,
        rank_snapshot=AcademicRank.LECTURER,
        department_snapshot=1,
    )


@pytest.fixture
def mocks() -> dict[str, MagicMock]:
    keeper = create_autospec(ScoreKeeper, instance=True)
    keeper.rubric_of.return_value = RUBRIC
    keeper.score.return_value = EntryScore(Decimal(1), Decimal(200))
    lecturer_dao = create_autospec(LecturerDAO, instance=True)
    lecturer_dao.get_by_id.return_value = ACTOR
    submission_dao = create_autospec(SubmissionDAO, instance=True)
    submission_dao.add.side_effect = lambda entity: entity
    return {
        "submission": submission_dao,
        "lecturer": lecturer_dao,
        "assessment": create_autospec(AssessmentDAO, instance=True),
        "position": create_autospec(MemberPositionDAO, instance=True),
        "keeper": keeper,
    }


@pytest.fixture
def entries(mocks: dict[str, MagicMock]) -> EntryService:
    return EntryService(
        mocks["submission"],
        create_autospec(RubricDAO, instance=True),
        mocks["lecturer"],
        create_autospec(EvidenceDAO, instance=True),
        create_autospec(ObjectStorage, instance=True),
        mocks["keeper"],
    )


@pytest.fixture
def assessments(mocks: dict[str, MagicMock]) -> AssessmentService:
    return AssessmentService(
        mocks["assessment"],
        mocks["submission"],
        mocks["position"],
        mocks["lecturer"],
        mocks["keeper"],
    )


def test_entry_gets_the_server_score_and_refreshes_totals(
    entries: EntryService, mocks: dict[str, MagicMock]
) -> None:
    mocks["submission"].get_by_id.return_value = submission(SubmissionStatus.DRAFT)
    mocks["submission"].count_entries.return_value = 0

    result = entries.create_entry(uuid4(), ACTOR.lecturer_id, EntryCreateRequest(item_id=1))

    assert result.score == Decimal(200)
    mocks["keeper"].refresh.assert_called_once()


def test_entries_of_a_sent_submission_are_locked(
    entries: EntryService, mocks: dict[str, MagicMock]
) -> None:
    mocks["submission"].get_by_id.return_value = submission(SubmissionStatus.SUBMITTED)

    with pytest.raises(ConflictError):
        entries.create_entry(uuid4(), ACTOR.lecturer_id, EntryCreateRequest(item_id=1))
    mocks["submission"].add.assert_not_called()


def test_entry_item_must_belong_to_the_round_rubric(
    entries: EntryService, mocks: dict[str, MagicMock]
) -> None:
    mocks["submission"].get_by_id.return_value = submission(SubmissionStatus.DRAFT)

    with pytest.raises(BadRequestError, match="item_id"):
        entries.create_entry(uuid4(), ACTOR.lecturer_id, EntryCreateRequest(item_id=99))


def test_section_max_entries_is_enforced(
    entries: EntryService, mocks: dict[str, MagicMock]
) -> None:
    mocks["submission"].get_by_id.return_value = submission(SubmissionStatus.DRAFT)
    mocks["submission"].count_entries.return_value = 2

    with pytest.raises(BadRequestError, match="at most 2"):
        entries.create_entry(uuid4(), ACTOR.lecturer_id, EntryCreateRequest(item_id=1))


def ranged_entry(mocks: dict[str, MagicMock], status: SubmissionStatus) -> SubmissionEntry:
    entry = SubmissionEntry(submission_id=uuid4(), item_id=2)
    mocks["submission"].get_entry.return_value = entry
    mocks["submission"].get_by_id.return_value = submission(status)
    return entry


def test_assessor_needs_the_item_position(
    assessments: AssessmentService, mocks: dict[str, MagicMock]
) -> None:
    entry = ranged_entry(mocks, SubmissionStatus.ASSESSING)
    mocks["position"].list_active.return_value = [
        MemberPosition(
            lecturer_id=ACTOR.lecturer_id,
            position=PositionCode.DEPT_CHAIR,
            department_id=1,
            start_date=date(2024, 1, 1),
        )
    ]

    with pytest.raises(ForbiddenError, match="exec_committee"):
        assessments.put_my_assessment(
            entry.id, ACTOR.lecturer_id, AssessmentPutRequest(value_given=Decimal("1.5"))
        )


def test_owner_cannot_assess_own_submission(
    assessments: AssessmentService, mocks: dict[str, MagicMock]
) -> None:
    entry = ranged_entry(mocks, SubmissionStatus.ASSESSING)
    mocks["submission"].get_by_id.return_value = submission(SubmissionStatus.ASSESSING, ACTOR)

    with pytest.raises(ForbiddenError, match="own"):
        assessments.put_my_assessment(
            entry.id, ACTOR.lecturer_id, AssessmentPutRequest(value_given=Decimal("1.5"))
        )


def test_assessing_only_while_status_is_assessing(
    assessments: AssessmentService, mocks: dict[str, MagicMock]
) -> None:
    entry = ranged_entry(mocks, SubmissionStatus.DRAFT)

    with pytest.raises(ConflictError, match="not assessing"):
        assessments.put_my_assessment(
            entry.id, ACTOR.lecturer_id, AssessmentPutRequest(value_given=Decimal("1.5"))
        )


def test_single_item_takes_one_assessor(
    assessments: AssessmentService, mocks: dict[str, MagicMock]
) -> None:
    entry = ranged_entry(mocks, SubmissionStatus.ASSESSING)
    mocks["position"].list_active.return_value = [
        MemberPosition(
            lecturer_id=ACTOR.lecturer_id,
            position=PositionCode.EXEC_COMMITTEE,
            start_date=date(2024, 1, 1),
        )
    ]
    mocks["assessment"].get_by_entry_and_assessor.return_value = None
    mocks["assessment"].list_by_entry.return_value = [
        EntryAssessment(
            entry_id=entry.id,
            assessor_id=uuid4(),
            position_used=PositionCode.EXEC_COMMITTEE,
            value_given=Decimal("1.2"),
        )
    ]

    with pytest.raises(ConflictError, match="one assessor"):
        assessments.put_my_assessment(
            entry.id, ACTOR.lecturer_id, AssessmentPutRequest(value_given=Decimal("1.5"))
        )
