"""Submission rules with mocked DAOs: creating, the approval workflow, rank mapping."""

from decimal import Decimal
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest

from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.v2.daos.evaluation_round_dao import EvaluationRoundDAO
from app.v2.daos.evidence_dao import EvidenceDAO
from app.v2.daos.lecturer_dao import LecturerDAO
from app.v2.daos.submission_dao import SubmissionDAO
from app.v2.dtos.submission_dto import ApprovalCreateRequest, SubmissionCreateRequest
from app.v2.models.enums import AcademicRank, ApprovalDecision, SignerRole, SubmissionStatus
from app.v2.models.lecturer import Lecturer
from app.v2.models.submission import EvaluationRound, Submission
from app.v2.services.score_keeper import ScoreKeeper
from app.v2.services.submission_service import SubmissionService, rank_from_text
from app.v2.storage.object_storage import ObjectStorage


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    return {
        "submission": create_autospec(SubmissionDAO, instance=True),
        "round": create_autospec(EvaluationRoundDAO, instance=True),
        "lecturer": create_autospec(LecturerDAO, instance=True),
        "evidence": create_autospec(EvidenceDAO, instance=True),
        "keeper": create_autospec(ScoreKeeper, instance=True),
    }


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> SubmissionService:
    daos["submission"].add.side_effect = lambda entity: entity
    daos["submission"].update.side_effect = lambda entity, values: (
        entity.sqlmodel_update(values) or entity
    )
    return SubmissionService(
        daos["submission"],
        daos["round"],
        daos["lecturer"],
        daos["evidence"],
        create_autospec(ObjectStorage, instance=True),
        daos["keeper"],
    )


def lecturer(**values: object) -> Lecturer:
    return Lecturer(name_th="สมชาย", email="a@x.th", department_id=1, **values)


def submission(status: SubmissionStatus, owner: Lecturer) -> Submission:
    return Submission(
        round_id=1,
        lecturer_id=owner.lecturer_id,
        status=status,
        rank_snapshot=AcademicRank.LECTURER,
        department_snapshot=1,
    )


@pytest.mark.parametrize(
    ("text", "rank"),
    [
        (None, AcademicRank.LECTURER),
        ("อาจารย์", AcademicRank.LECTURER),
        ("ผู้ช่วยศาสตราจารย์", AcademicRank.ASST_PROF),
        ("ผศ.ดร.", AcademicRank.ASST_PROF),
        ("รองศาสตราจารย์", AcademicRank.ASSOC_PROF),
        ("ศาสตราจารย์", AcademicRank.PROF),
        ("Assistant Professor", AcademicRank.ASST_PROF),
        ("prof", AcademicRank.PROF),
    ],
)
def test_rank_from_text(text: str | None, rank: AcademicRank) -> None:
    assert rank_from_text(text) is rank


def test_unknown_rank_is_rejected() -> None:
    with pytest.raises(BadRequestError):
        rank_from_text("นักวิจัย")


def test_create_submission_needs_an_open_round(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer()
    daos["lecturer"].get_by_id.return_value = owner
    daos["round"].get_by_id.return_value = EvaluationRound(id=1, is_open=False)

    with pytest.raises(ConflictError, match="not open"):
        service.create_submission(owner.lecturer_id, SubmissionCreateRequest(round_id=1))


def test_create_submission_snapshots_rank_and_department(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer(rank="รองศาสตราจารย์")
    daos["lecturer"].get_by_id.return_value = owner
    daos["round"].get_by_id.return_value = EvaluationRound(id=1, is_open=True)
    daos["submission"].get_by_round_and_lecturer.return_value = None

    result = service.create_submission(owner.lecturer_id, SubmissionCreateRequest(round_id=1))

    assert (result.rank_snapshot, result.department_snapshot) == (AcademicRank.ASSOC_PROF, 1)
    assert result.status is SubmissionStatus.DRAFT


def test_unknown_caller_is_unauthorized(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    daos["lecturer"].get_by_id.return_value = None
    with pytest.raises(UnauthorizedError):
        service.create_submission(uuid4(), SubmissionCreateRequest(round_id=1))


@pytest.mark.parametrize(
    ("status", "role", "next_status"),
    [
        (SubmissionStatus.DRAFT, SignerRole.PERFORMER, SubmissionStatus.SUBMITTED),
        (SubmissionStatus.SUBMITTED, SignerRole.RECEIVER, SubmissionStatus.ASSESSING),
        (SubmissionStatus.DEPT_REVIEW, SignerRole.DEPT_COMMITTEE, SubmissionStatus.DEPT_APPROVED),
        (SubmissionStatus.DEPT_APPROVED, SignerRole.RECEIVER, SubmissionStatus.SENT_TO_FACULTY),
    ],
)
def test_approving_moves_the_submission_on(
    service: SubmissionService,
    daos: dict[str, MagicMock],
    status: SubmissionStatus,
    role: SignerRole,
    next_status: SubmissionStatus,
) -> None:
    owner = lecturer(rank="อาจารย์")
    current = submission(status, owner)
    daos["submission"].get_by_id.return_value = current
    daos["lecturer"].get_by_id.return_value = owner

    approval = service.create_approval(
        current.id, owner.lecturer_id, ApprovalCreateRequest(decision=ApprovalDecision.APPROVED)
    )

    assert approval.role is role
    assert current.status is next_status


def test_sending_freezes_the_totals(service: SubmissionService, daos: dict[str, MagicMock]) -> None:
    owner = lecturer()
    current = submission(SubmissionStatus.RETURNED, owner)
    daos["submission"].get_by_id.return_value = current
    daos["lecturer"].get_by_id.return_value = owner

    service.create_approval(
        current.id, owner.lecturer_id, ApprovalCreateRequest(decision=ApprovalDecision.APPROVED)
    )

    assert current.submitted_at is not None
    daos["keeper"].refresh.assert_called_once()
    assert daos["keeper"].refresh.call_args.kwargs == {"freeze": True}


def test_leaving_assessing_needs_every_assessment(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer()
    daos["submission"].get_by_id.return_value = submission(SubmissionStatus.ASSESSING, owner)
    daos["lecturer"].get_by_id.return_value = owner
    daos["keeper"].pending_assessments.return_value = 2

    with pytest.raises(ConflictError, match="2 entries"):
        service.create_approval(
            uuid4(), owner.lecturer_id, ApprovalCreateRequest(decision=ApprovalDecision.APPROVED)
        )
    daos["submission"].add.assert_not_called()


def test_returning_needs_a_comment_and_cannot_happen_on_a_draft(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer()
    daos["lecturer"].get_by_id.return_value = owner
    returned = ApprovalCreateRequest(decision=ApprovalDecision.RETURNED)

    daos["submission"].get_by_id.return_value = submission(SubmissionStatus.SUBMITTED, owner)
    with pytest.raises(BadRequestError, match="comment"):
        service.create_approval(uuid4(), owner.lecturer_id, returned)

    daos["submission"].get_by_id.return_value = submission(SubmissionStatus.DRAFT, owner)
    with pytest.raises(ConflictError):
        service.create_approval(
            uuid4(), owner.lecturer_id, returned.model_copy(update={"comment": "x"})
        )


def test_finished_submission_cannot_change(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer()
    daos["lecturer"].get_by_id.return_value = owner
    daos["submission"].get_by_id.return_value = submission(SubmissionStatus.SENT_TO_FACULTY, owner)

    with pytest.raises(ConflictError):
        service.create_approval(
            uuid4(), owner.lecturer_id, ApprovalCreateRequest(decision=ApprovalDecision.APPROVED)
        )


def test_only_a_draft_can_be_deleted(
    service: SubmissionService, daos: dict[str, MagicMock]
) -> None:
    owner = lecturer()
    daos["lecturer"].get_by_id.return_value = owner
    daos["submission"].get_by_id.return_value = submission(SubmissionStatus.SUBMITTED, owner)

    with pytest.raises(ConflictError):
        service.delete_submission(uuid4(), owner.lecturer_id)
    daos["submission"].delete.assert_not_called()


def test_score_fields_are_decimals() -> None:
    assert isinstance(Submission.model_fields["raw_total"].default, Decimal)
