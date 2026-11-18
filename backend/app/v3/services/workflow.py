"""Who signs a submission at each status, and where it goes next.

Every change of status is one row in `submission_approval` (append-only). The signer's
role comes from the current status, never from the request body.

    draft / returned  --performer (owner) sends---------->  submitted
    submitted         --reviewer forwards to the head---->  assessing
    assessing         --dept_chair checks, sends on------>  sent_to_faculty

The reviewer is the lecturer assigned to the owner in that round (reviewer_assignment). If
nobody is assigned, the department head may sign the first step (SubmissionService), so a
sheet is never stuck. Staff and the committee are not part of the flow.

From submitted onwards the signer may return it instead (status -> returned), and the
owner fixes the entries and sends it again. While it is still `submitted` (nobody has
signed it) the owner may also pull it back to `returned` (SubmissionService.create_approval).
Change this table to change the workflow.
Who may sign each role: app/v3/services/access.py (can_sign).
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
    SubmissionStatus.SUBMITTED: Step(SignerRole.REVIEWER, SubmissionStatus.ASSESSING, True),
    SubmissionStatus.ASSESSING: Step(SignerRole.DEPT_CHAIR, SubmissionStatus.SENT_TO_FACULTY, True),
}

# The owner may add, change or delete entries and evidence only in these statuses
# (the database trigger from 003/004 enforces the same rule for entries).
EDITABLE_STATUSES = frozenset({SubmissionStatus.DRAFT, SubmissionStatus.RETURNED})
