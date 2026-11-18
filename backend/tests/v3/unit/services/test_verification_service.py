from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, ForbiddenError
from app.v2.models.enums import (
    AcademicRank,
    EvidenceStatus,
    SubmissionStatus,
    VerificationStatus,
)
from app.v2.models.lecturer import Lecturer
from app.v2.models.publication import Publication
from app.v2.models.reviewer_assignment import ReviewerAssignment
from app.v2.models.submission import EntryEvidence, Submission, SubmissionEntry
from app.v2.models.submission_review import SubmissionReview
from app.v3.daos.evidence_dao import EvidenceDAO
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.reviewer_assignment_dao import ReviewerAssignmentDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.daos.submission_review_dao import SubmissionReviewDAO
from app.v3.daos.verification_dao import VerificationDAO
from app.v3.dtos.publication_dto import PublicationUpdateRequest
from app.v3.dtos.verification_dto import VerificationPutRequest, VerificationQueueQuery
from app.v3.security import Actor, Role
from app.v3.services.publication_service import PublicationService
from app.v3.services.verification_service import VerificationService

AUTHOR = uuid4()
REVIEWER = Actor(uuid4(), frozenset({Role.LECTURER, Role.REVIEWER}))
VERIFY = VerificationPutRequest(status=VerificationStatus.VERIFIED)


@pytest.fixture
def daos() -> dict[str, MagicMock]:
    daos = {
        "verification": create_autospec(VerificationDAO, instance=True),
        "publication": create_autospec(PublicationDAO, instance=True),
        "evidence": create_autospec(EvidenceDAO, instance=True),
        "submission": create_autospec(SubmissionDAO, instance=True),
        "assignment": create_autospec(ReviewerAssignmentDAO, instance=True),
        "review": create_autospec(SubmissionReviewDAO, instance=True),
        "lecturer": create_autospec(LecturerDAO, instance=True),
    }
    daos["assignment"].reviewee_ids.return_value = [AUTHOR]
    daos["assignment"].is_assigned.return_value = True
    daos["publication"].get_by_id.return_value = Publication(publication_id=1, title="T")
    daos["publication"].get_author_ids.return_value = [AUTHOR]
    for name in ("publication", "evidence"):
        daos[name].update.side_effect = lambda row, values: row.sqlmodel_update(values) or row
    return daos


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> VerificationService:
    return VerificationService(
        daos["verification"],
        daos["publication"],
        daos["evidence"],
        daos["submission"],
        daos["assignment"],
        daos["review"],
        daos["lecturer"],
    )


def test_reviewer_verifies_a_publication(service: VerificationService) -> None:
    result = service.set_publication_verification(1, REVIEWER, VERIFY)

    assert result.verification_status is VerificationStatus.VERIFIED
    assert result.verified_by == REVIEWER.lecturer_id
    assert result.verified_at is not None


def test_back_to_pending_clears_the_reviewer(service: VerificationService) -> None:
    service.set_publication_verification(1, REVIEWER, VERIFY)

    result = service.set_publication_verification(
        1, REVIEWER, VerificationPutRequest(status=VerificationStatus.PENDING)
    )

    assert (result.verified_by, result.verified_at) == (None, None)


def test_nobody_verifies_their_own_publication(service: VerificationService) -> None:
    author_reviewer = Actor(AUTHOR, frozenset({Role.LECTURER, Role.REVIEWER}))

    with pytest.raises(ForbiddenError, match="own"):
        service.set_publication_verification(1, author_reviewer, VERIFY)


def test_rejecting_needs_a_note() -> None:
    with pytest.raises(ValidationError, match="note"):
        VerificationPutRequest(status=VerificationStatus.REJECTED)


def evidence_of(owner, status: EvidenceStatus) -> tuple[EntryEvidence, Submission]:
    submission = Submission(
        id=uuid4(),
        round_id=1,
        lecturer_id=owner,
        rank_snapshot=AcademicRank.LECTURER,
        department_snapshot=1,
    )
    entry = SubmissionEntry(id=uuid4(), submission_id=submission.id, item_id=1)
    evidence = EntryEvidence(
        id=uuid4(),
        entry_id=entry.id,
        s3_key="k",
        file_name="f.pdf",
        mime_type="application/pdf",
        size_bytes=1,
        status=status,
        uploaded_by=owner,
    )
    return evidence, submission, entry


@pytest.mark.parametrize(
    ("owner", "status", "error"),
    [
        (AUTHOR, EvidenceStatus.PENDING, ConflictError),
        (REVIEWER.lecturer_id, EvidenceStatus.UPLOADED, ForbiddenError),
        (AUTHOR, EvidenceStatus.UPLOADED, None),
    ],
    ids=["not-uploaded-yet", "own-submission", "ok"],
)
def test_evidence_verification(
    service: VerificationService, daos: dict[str, MagicMock], owner, status, error
) -> None:
    evidence, submission, entry = evidence_of(owner, status)
    daos["evidence"].get_by_id.return_value = evidence
    daos["submission"].get_entry.return_value = entry
    daos["submission"].get_by_id.return_value = submission

    if error:
        with pytest.raises(error):
            service.set_evidence_verification(evidence.id, REVIEWER, VERIFY)
    else:
        result = service.set_evidence_verification(evidence.id, REVIEWER, VERIFY)
        assert result.verification_status is VerificationStatus.VERIFIED


# --- effect on publications -----------------------------------------------------------


@pytest.fixture
def publications(daos: dict[str, MagicMock]) -> PublicationService:
    lecturer_dao = MagicMock()
    return PublicationService(daos["publication"], lecturer_dao)


def test_a_verified_publication_is_locked_for_its_authors(
    publications: PublicationService, daos: dict[str, MagicMock]
) -> None:
    daos["publication"].get_by_id.return_value.verification_status = VerificationStatus.VERIFIED
    author = Actor(AUTHOR, frozenset({Role.LECTURER}))

    with pytest.raises(ForbiddenError, match="verified"):
        publications.update_publication(1, PublicationUpdateRequest(volume="2"), actor=author)
    with pytest.raises(ForbiddenError, match="verified"):
        publications.delete_publication(1, actor=author)

    staff = Actor(uuid4(), frozenset({Role.LECTURER, Role.STAFF}))
    publications.update_publication(1, PublicationUpdateRequest(volume="2"), actor=staff)


def test_an_authors_fix_sends_a_rejected_publication_back_to_pending(
    publications: PublicationService, daos: dict[str, MagicMock]
) -> None:
    daos["publication"].get_by_id.return_value.verification_status = VerificationStatus.REJECTED
    daos["publication"].get_by_doi.return_value = None
    author = Actor(AUTHOR, frozenset({Role.LECTURER}))

    publications.update_publication(1, PublicationUpdateRequest(volume="2"), actor=author)

    values = daos["publication"].update.call_args.args[1]
    assert values["verification_status"] is VerificationStatus.PENDING


# --- reviewer assignment narrows the queue (V4 #293) ---------------------------------


def test_a_plain_reviewer_only_sees_their_assigned_reviewees(
    service: VerificationService, daos: dict[str, MagicMock]
) -> None:
    daos["verification"].find_publications.return_value = ([], 0)
    daos["verification"].find_evidence.return_value = ([], 0)
    reviewee = uuid4()
    daos["assignment"].reviewee_ids.return_value = [reviewee]

    service.list_publication_queue(REVIEWER, VerificationQueueQuery())
    service.list_evidence_queue(REVIEWER, VerificationQueueQuery())

    daos["assignment"].reviewee_ids.assert_called_with(REVIEWER.lecturer_id)
    assert daos["verification"].find_publications.call_args.kwargs["reviewee_ids"] == [reviewee]
    assert daos["verification"].find_evidence.call_args.kwargs["reviewee_ids"] == [reviewee]


@pytest.mark.parametrize("role", [Role.EXECUTIVE, Role.STAFF, Role.ADMIN])
def test_only_a_real_reviewer_can_use_the_queue_or_verify(
    service: VerificationService, daos: dict[str, MagicMock], role: Role
) -> None:
    """Staff, executives and admins may read sheets but never verify (unless also assigned)."""
    caller = Actor(uuid4(), frozenset({Role.LECTURER, role}))
    evidence, submission, entry = evidence_of(AUTHOR, EvidenceStatus.UPLOADED)
    daos["evidence"].get_by_id.return_value = evidence
    daos["submission"].get_entry.return_value = entry
    daos["submission"].get_by_id.return_value = submission

    with pytest.raises(ForbiddenError, match="reviewer"):
        service.list_publication_queue(caller, VerificationQueueQuery())
    with pytest.raises(ForbiddenError, match="reviewer"):
        service.list_evidence_queue(caller, VerificationQueueQuery())
    with pytest.raises(ForbiddenError, match="reviewer"):
        service.set_publication_verification(1, caller, VERIFY)
    with pytest.raises(ForbiddenError, match="reviewer"):
        service.set_evidence_verification(evidence.id, caller, VERIFY)
    daos["publication"].update.assert_not_called()
    daos["evidence"].update.assert_not_called()


def test_a_reviewer_cannot_verify_a_publication_of_someone_they_are_not_assigned_to(
    service: VerificationService, daos: dict[str, MagicMock]
) -> None:
    daos["assignment"].reviewee_ids.return_value = [uuid4()]  # not the author

    with pytest.raises(ForbiddenError, match="not assigned"):
        service.set_publication_verification(1, REVIEWER, VERIFY)
    daos["publication"].update.assert_not_called()


def test_a_reviewer_cannot_verify_evidence_outside_their_assignment_for_that_round(
    service: VerificationService, daos: dict[str, MagicMock]
) -> None:
    evidence, submission, entry = evidence_of(AUTHOR, EvidenceStatus.UPLOADED)
    daos["evidence"].get_by_id.return_value = evidence
    daos["submission"].get_entry.return_value = entry
    daos["submission"].get_by_id.return_value = submission
    daos["assignment"].is_assigned.return_value = False

    with pytest.raises(ForbiddenError, match="not assigned"):
        service.set_evidence_verification(evidence.id, REVIEWER, VERIFY)

    daos["assignment"].is_assigned.assert_called_with(
        REVIEWER.lecturer_id, AUTHOR, submission.round_id
    )
    daos["evidence"].update.assert_not_called()


# --- whole-sheet verdict (V4 #335) ----------------------------------------------------


def sheet(owner, status: SubmissionStatus = SubmissionStatus.SUBMITTED) -> Submission:
    return Submission(
        id=uuid4(),
        round_id=3,
        lecturer_id=owner,
        status=status,
        rank_snapshot=AcademicRank.LECTURER,
        department_snapshot=1,
    )


@pytest.fixture
def reviews(daos: dict[str, MagicMock]) -> dict[str, MagicMock]:
    daos["review"].get.return_value = None
    daos["review"].add.side_effect = lambda row: row
    daos["review"].update.side_effect = lambda row, values: row.sqlmodel_update(values) or row
    return daos


def test_the_assigned_reviewer_writes_a_verdict_on_a_submitted_sheet(
    service: VerificationService, reviews: dict[str, MagicMock]
) -> None:
    target = sheet(AUTHOR)
    reviews["submission"].get_by_id.return_value = target

    result = service.set_submission_review(
        target.id,
        REVIEWER,
        VerificationPutRequest(status=VerificationStatus.REJECTED, note="ขาดหลักฐานข้อ 1.2"),
    )

    assert (result.status, result.note) == (VerificationStatus.REJECTED, "ขาดหลักฐานข้อ 1.2")
    assert result.reviewed_by == REVIEWER.lecturer_id
    reviews["assignment"].is_assigned.assert_called_with(REVIEWER.lecturer_id, AUTHOR, 3)
    # the verdict never touches the sheet itself
    reviews["submission"].update.assert_not_called()


def test_a_second_verdict_updates_the_same_row(
    service: VerificationService, reviews: dict[str, MagicMock]
) -> None:
    target = sheet(AUTHOR)
    reviews["submission"].get_by_id.return_value = target
    reviews["review"].get.return_value = SubmissionReview(
        submission_id=target.id, status=VerificationStatus.REJECTED, note="x"
    )

    result = service.set_submission_review(target.id, REVIEWER, VERIFY)

    assert result.status is VerificationStatus.VERIFIED
    reviews["review"].add.assert_not_called()
    reviews["review"].update.assert_called_once()


@pytest.mark.parametrize(
    ("owner", "status", "assigned", "error", "match"),
    [
        (AUTHOR, SubmissionStatus.DRAFT, True, ConflictError, "not been submitted"),
        (REVIEWER.lecturer_id, SubmissionStatus.SUBMITTED, True, ForbiddenError, "own"),
        (AUTHOR, SubmissionStatus.SUBMITTED, False, ForbiddenError, "not assigned"),
    ],
    ids=["draft", "own-sheet", "not-assigned-in-that-round"],
)
def test_sheet_verdict_refusals(
    service: VerificationService,
    reviews: dict[str, MagicMock],
    owner,
    status,
    assigned,
    error,
    match,
) -> None:
    target = sheet(owner, status)
    reviews["submission"].get_by_id.return_value = target
    reviews["assignment"].is_assigned.return_value = assigned

    with pytest.raises(error, match=match):
        service.set_submission_review(target.id, REVIEWER, VERIFY)

    reviews["review"].add.assert_not_called()


@pytest.mark.parametrize("role", [Role.STAFF, Role.EXECUTIVE, Role.ADMIN])
def test_only_a_real_reviewer_writes_a_sheet_verdict(
    service: VerificationService, reviews: dict[str, MagicMock], role: Role
) -> None:
    target = sheet(AUTHOR)
    reviews["submission"].get_by_id.return_value = target
    caller = Actor(uuid4(), frozenset({Role.LECTURER, role}))

    with pytest.raises(ForbiddenError, match="reviewer"):
        service.set_submission_review(target.id, caller, VERIFY)


def test_a_sheet_nobody_looked_at_reads_as_pending(
    service: VerificationService, reviews: dict[str, MagicMock]
) -> None:
    target = sheet(AUTHOR)
    reviews["submission"].get_by_id.return_value = target
    owner = Actor(AUTHOR, frozenset({Role.LECTURER}))

    result = service.get_submission_review(target.id, owner)

    assert result.status is VerificationStatus.PENDING
    assert result.reviewed_by is None


def test_my_assignments_come_with_sheet_verdict_and_pending_counts_newest_round_first(
    service: VerificationService, reviews: dict[str, MagicMock]
) -> None:
    mine = REVIEWER.lecturer_id
    ann, bob = uuid4(), uuid4()
    reviews["assignment"].list_by_reviewer.return_value = [
        ReviewerAssignment(round_id=2, reviewer_id=mine, reviewee_id=bob, assigned_by=mine),
        ReviewerAssignment(round_id=3, reviewer_id=mine, reviewee_id=ann, assigned_by=mine),
        ReviewerAssignment(round_id=3, reviewer_id=mine, reviewee_id=bob, assigned_by=mine),
    ]
    names = {ann: "Ann", bob: "Bob"}
    reviews["lecturer"].get_by_id.side_effect = lambda lecturer_id: Lecturer(
        lecturer_id=lecturer_id, name_th=names[lecturer_id], email="x@x"
    )
    ann_sheet = sheet(ann)
    reviews["submission"].get_by_round_and_lecturer.side_effect = lambda round_id, lecturer_id: (
        ann_sheet if (round_id, lecturer_id) == (3, ann) else None
    )
    reviews["review"].get.return_value = SubmissionReview(
        submission_id=ann_sheet.id, status=VerificationStatus.VERIFIED
    )
    reviews["verification"].count_pending_evidence.return_value = 4
    reviews["verification"].count_pending_publications.return_value = 2

    items = service.list_assignments(REVIEWER)

    assert [(item.round_id, item.reviewee_name_th) for item in items] == [
        (3, "Ann"),
        (3, "Bob"),
        (2, "Bob"),
    ]
    first, second, _ = items
    assert (first.submission_id, first.review_status, first.pending_evidence) == (
        ann_sheet.id,
        VerificationStatus.VERIFIED,
        4,
    )
    # no sheet yet: nothing to verdict, nothing pending on a sheet, publications still count
    assert (second.submission_id, second.review_status, second.pending_evidence) == (None, None, 0)
    assert second.pending_publications == 2
