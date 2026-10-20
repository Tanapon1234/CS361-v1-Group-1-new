"""Checks of docs/v2/permissions.md that need data, so they cannot live in ROUTE_RULES."""

from uuid import UUID

from app.core.exceptions import ForbiddenError
from app.v2.models.enums import PositionCode, SignerRole
from app.v2.models.submission import Submission
from app.v3.permissions import DEPARTMENT_SIGNERS
from app.v3.security import Actor, Role

_SIGNER_LABEL = {
    SignerRole.PERFORMER: "owner of the submission",
    SignerRole.RECEIVER: "faculty staff (staff role)",
    SignerRole.DEPT_CHAIR: "chair of the submission's department",
    SignerRole.DEPT_COMMITTEE: "a committee member of the submission's department",
}


def signer_departments(actor: Actor) -> frozenset[int]:
    """Departments whose submissions the caller sees as dept chair / committee."""
    return actor.department_ids_with(*DEPARTMENT_SIGNERS)


def can_view_submission(actor: Actor, submission: Submission) -> bool:
    return (
        actor.is_lecturer(submission.lecturer_id)
        or actor.views_all
        or submission.department_snapshot in signer_departments(actor)
    )


def require_view_submission(actor: Actor, submission: Submission) -> None:
    if not can_view_submission(actor, submission):
        raise ForbiddenError("You may not see this submission")


def require_owner(actor_id: UUID, submission: Submission) -> None:
    if submission.lecturer_id != actor_id:
        raise ForbiddenError("Only the owner can change this submission")


def require_department_view(actor: Actor, department_id: int | None) -> int | None:
    """Department to filter a list by: any (or the asked one) for viewers of everything;
    a department signer only gets their own department."""
    if actor.views_all:
        return department_id
    allowed = signer_departments(actor)
    if department_id is None and len(allowed) == 1:
        return next(iter(allowed))
    if department_id is None or department_id not in allowed:
        raise ForbiddenError("Choose a department where you are chair or committee (department_id)")
    return department_id


def can_sign(actor: Actor, submission: Submission, role: SignerRole) -> bool:
    """Signatures are personal: admin does not stand in for the owner or a position holder."""
    department = submission.department_snapshot
    match role:
        case SignerRole.PERFORMER:
            return actor.is_lecturer(submission.lecturer_id)
        case SignerRole.RECEIVER:
            return actor.has_any(Role.STAFF)
        case SignerRole.DEPT_CHAIR:
            return actor.holds(PositionCode.DEPT_CHAIR, department)
        case SignerRole.DEPT_COMMITTEE:
            return actor.holds(PositionCode.DEPT_COMMITTEE, department)
    return False


def require_signer(actor: Actor, submission: Submission, role: SignerRole) -> None:
    if not can_sign(actor, submission, role):
        raise ForbiddenError(f"This step is signed by the {_SIGNER_LABEL[role]}")
