"""Who signs a submission at each status, and where it goes next.

Every change of status is one row in `submission_approval` (append-only). The signer's
role comes from the current status, never from the request body.

    draft / returned  --performer (owner) sends---------->  submitted
    submitted         --receiver accepts----------------->  assessing
    assessing         --dept_chair (assessments done)---->  dept_review
    dept_review       --dept_committee approves---------->  dept_approved
    dept_approved     --receiver sends to the faculty---->  sent_to_faculty

From submitted onwards the signer may return it instead (status -> returned), and the
owner fixes the entries and sends it again. Change this table to change the workflow.
"""

from dataclasses import dataclass

from app.v2.models.enums import SignerRole, SubmissionStatus


@dataclass(frozen=True, slots=True)
class Step:
    role: SignerRole
    on_approve: SubmissionStatus
    can_return: bool


STEPS: dict[SubmissionStatus, Step] = {
    SubmissionStatus.DRAFT: Step(SignerRole.PERFORMER, SubmissionStatus.SUBMITTED, False),
    SubmissionStatus.RETURNED: Step(SignerRole.PERFORMER, SubmissionStatus.SUBMITTED, False),
    SubmissionStatus.SUBMITTED: Step(SignerRole.RECEIVER, SubmissionStatus.ASSESSING, True),
    SubmissionStatus.ASSESSING: Step(SignerRole.DEPT_CHAIR, SubmissionStatus.DEPT_REVIEW, True),
    SubmissionStatus.DEPT_REVIEW: Step(
        SignerRole.DEPT_COMMITTEE, SubmissionStatus.DEPT_APPROVED, True
    ),
    SubmissionStatus.DEPT_APPROVED: Step(
        SignerRole.RECEIVER, SubmissionStatus.SENT_TO_FACULTY, True
    ),
}

# The owner may add, change or delete entries and evidence only in these statuses
# (the database trigger from 003/004 enforces the same rule for entries).
EDITABLE_STATUSES = frozenset({SubmissionStatus.DRAFT, SubmissionStatus.RETURNED})
