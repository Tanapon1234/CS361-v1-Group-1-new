from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictError, ForbiddenError
from app.v2.models.enums import AcademicRank, EvidenceStatus, VerificationStatus
from app.v2.models.publication import Publication
from app.v2.models.submission import EntryEvidence, Submission, SubmissionEntry
from app.v3.daos.evidence_dao import EvidenceDAO
from app.v3.daos.publication_dao import PublicationDAO
from app.v3.daos.submission_dao import SubmissionDAO
from app.v3.daos.verification_dao import VerificationDAO
from app.v3.dtos.publication_dto import PublicationUpdateRequest
from app.v3.dtos.verification_dto import VerificationPutRequest
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
    }
    daos["publication"].get_by_id.return_value = Publication(publication_id=1, title="T")
    daos["publication"].get_author_ids.return_value = [AUTHOR]
    for name in ("publication", "evidence"):
        daos[name].update.side_effect = lambda row, values: row.sqlmodel_update(values) or row
    return daos


@pytest.fixture
def service(daos: dict[str, MagicMock]) -> VerificationService:
    return VerificationService(
        daos["verification"], daos["publication"], daos["evidence"], daos["submission"]
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
