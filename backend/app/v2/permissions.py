"""Who may call which /api/v2 endpoint: docs/v2/permissions.md as code.

The api_v2 router checks every request against ROUTE_RULES before the controller runs.
A route with no rule is refused, and tests/v2/test_permissions.py fails until it has one.
Rules decide from the caller alone (roles, positions, `lecturer_id` in the path); checks
that need data (owner of a submission, authors of a publication, department of a
lecturer) are in the services, see app/v2/services/access.py.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.v2.models.enums import PositionCode
from app.v2.security import VIEW_ALL_ROLES, Actor, Role

DEPARTMENT_SIGNERS = frozenset({PositionCode.DEPT_CHAIR, PositionCode.DEPT_COMMITTEE})


@dataclass(frozen=True, slots=True)
class Rule:
    """Allowed when any part matches. Admin is always allowed (Actor.has_any)."""

    roles: frozenset[Role] = frozenset()
    anyone: bool = False  # every signed-in caller
    self_param: str | None = None  # path parameter that is the caller's own lecturer_id
    positions: frozenset[PositionCode] = field(default_factory=frozenset)

    def allows(self, actor: Actor, path_params: Mapping[str, Any]) -> bool:
        if self.anyone or actor.has_any(*self.roles):
            return True
        own = self.self_param is not None and actor.lecturer_id is not None
        if own and str(path_params.get(self.self_param)) == str(actor.lecturer_id):
            return True
        return any(held.position in self.positions for held in actor.positions)


SIGNED_IN = Rule(anyone=True)
STAFF = Rule(roles=frozenset({Role.STAFF}))
SELF_OR_STAFF = Rule(roles=frozenset({Role.STAFF}), self_param="lecturer_id")
REVIEWERS = Rule(roles=frozenset({Role.REVIEWER}))
ADMIN = Rule(roles=frozenset({Role.ADMIN}))
# See everyone's data; department signers too, but services narrow them to their department
VIEWERS = Rule(roles=VIEW_ALL_ROLES, positions=DEPARTMENT_SIGNERS)
SELF_OR_VIEWERS = Rule(roles=VIEW_ALL_ROLES, positions=DEPARTMENT_SIGNERS, self_param="lecturer_id")

# (method, path without the /api/v2 prefix) -> rule
ROUTE_RULES: dict[tuple[str, str], Rule] = {
    # lecturer
    ("GET", "/lecturers"): SIGNED_IN,
    ("POST", "/lecturers"): STAFF,
    ("GET", "/lecturers/{lecturer_id}"): SIGNED_IN,
    # self may edit contact fields only (LecturerService.update_lecturer)
    ("PATCH", "/lecturers/{lecturer_id}"): SELF_OR_STAFF,
    ("POST", "/lecturers/{lecturer_id}/activate"): STAFF,
    ("POST", "/lecturers/{lecturer_id}/deactivate"): STAFF,
    # profile image / cv
    ("GET", "/lecturers/{lecturer_id}/profile-image"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/profile-image/presign"): SELF_OR_STAFF,
    ("POST", "/lecturers/{lecturer_id}/profile-image/complete"): SELF_OR_STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/profile-image"): SELF_OR_STAFF,
    ("GET", "/lecturers/{lecturer_id}/cv"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/cv/presign"): SELF_OR_STAFF,
    ("POST", "/lecturers/{lecturer_id}/cv/complete"): SELF_OR_STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/cv"): SELF_OR_STAFF,
    # education
    ("GET", "/lecturers/{lecturer_id}/educations"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/educations"): SELF_OR_STAFF,
    ("PATCH", "/lecturers/{lecturer_id}/educations/{education_id}"): SELF_OR_STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/educations/{education_id}"): SELF_OR_STAFF,
    # research interests: anyone may add a topic to the master list
    ("GET", "/research-interests"): SIGNED_IN,
    ("POST", "/research-interests"): SIGNED_IN,
    ("PATCH", "/research-interests/{research_interest_id}"): STAFF,
    ("DELETE", "/research-interests/{research_interest_id}"): STAFF,
    ("GET", "/lecturers/{lecturer_id}/research-interests"): SIGNED_IN,
    ("PUT", "/lecturers/{lecturer_id}/research-interests"): SELF_OR_STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/research-interests/{research_interest_id}"): SELF_OR_STAFF,
    # publication profiles
    ("GET", "/lecturers/{lecturer_id}/publication-profiles"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/publication-profiles"): SELF_OR_STAFF,
    (
        "PATCH",
        "/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}",
    ): SELF_OR_STAFF,
    (
        "DELETE",
        "/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}",
    ): SELF_OR_STAFF,
    # publications: authors or staff edit (PublicationService)
    ("GET", "/publications"): SIGNED_IN,
    ("POST", "/publications"): SIGNED_IN,
    ("GET", "/publications/{publication_id}"): SIGNED_IN,
    ("PATCH", "/publications/{publication_id}"): SIGNED_IN,
    ("DELETE", "/publications/{publication_id}"): SIGNED_IN,
    ("GET", "/lecturers/{lecturer_id}/publications"): SIGNED_IN,
    # expertise
    ("GET", "/expertise"): SIGNED_IN,
    ("POST", "/expertise"): SIGNED_IN,
    ("GET", "/expertise/{expertise_id}"): SIGNED_IN,
    ("PATCH", "/expertise/{expertise_id}"): STAFF,
    ("DELETE", "/expertise/{expertise_id}"): STAFF,
    ("GET", "/lecturers/{lecturer_id}/expertise"): SIGNED_IN,
    ("PUT", "/lecturers/{lecturer_id}/expertise"): SELF_OR_STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/expertise/{expertise_id}"): SELF_OR_STAFF,
    # a lecturer's work by year: department signers only for their department (service)
    ("GET", "/lecturers/{lecturer_id}/work"): SELF_OR_VIEWERS,
    # --- workload ---
    ("GET", "/me"): SIGNED_IN,
    ("GET", "/departments"): SIGNED_IN,
    ("POST", "/departments"): STAFF,
    ("PATCH", "/departments/{department_id}"): STAFF,
    ("GET", "/lecturers/{lecturer_id}/positions"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/positions"): STAFF,
    ("PATCH", "/lecturers/{lecturer_id}/positions/{position_id}"): STAFF,
    ("DELETE", "/lecturers/{lecturer_id}/positions/{position_id}"): STAFF,
    # rubric
    ("GET", "/rubric-versions"): SIGNED_IN,
    ("POST", "/rubric-versions"): STAFF,
    ("GET", "/rubric-versions/{version_id}"): SIGNED_IN,
    ("PATCH", "/rubric-versions/{version_id}"): STAFF,
    ("GET", "/rubric-versions/{version_id}/form"): SIGNED_IN,
    ("GET", "/rubric-versions/{version_id}/categories"): SIGNED_IN,
    ("POST", "/rubric-versions/{version_id}/categories"): STAFF,
    ("GET", "/rubric-categories/{category_id}/sections"): SIGNED_IN,
    ("POST", "/rubric-categories/{category_id}/sections"): STAFF,
    ("PATCH", "/rubric-sections/{section_id}"): STAFF,
    ("DELETE", "/rubric-sections/{section_id}"): STAFF,
    ("GET", "/rubric-sections/{section_id}/items"): SIGNED_IN,
    ("POST", "/rubric-sections/{section_id}/items"): STAFF,
    ("PATCH", "/rubric-items/{item_id}"): STAFF,
    ("DELETE", "/rubric-items/{item_id}"): STAFF,
    # rounds
    ("GET", "/rounds"): SIGNED_IN,
    ("POST", "/rounds"): STAFF,
    ("GET", "/rounds/{round_id}"): SIGNED_IN,
    ("PATCH", "/rounds/{round_id}"): STAFF,
    ("GET", "/rounds/{round_id}/submissions"): VIEWERS,
    ("GET", "/rounds/{round_id}/report"): VIEWERS,
    # submissions, entries, evidence: owner / viewers decided per submission (access.py)
    ("GET", "/submissions"): SIGNED_IN,
    ("POST", "/submissions"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}"): SIGNED_IN,
    ("DELETE", "/submissions/{submission_id}"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}/summary"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}/totals"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}/pdf"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}/approvals"): SIGNED_IN,
    ("POST", "/submissions/{submission_id}/approvals"): SIGNED_IN,
    ("GET", "/submissions/{submission_id}/entries"): SIGNED_IN,
    ("POST", "/submissions/{submission_id}/entries"): SIGNED_IN,
    ("GET", "/entries/{entry_id}"): SIGNED_IN,
    ("PATCH", "/entries/{entry_id}"): SIGNED_IN,
    ("DELETE", "/entries/{entry_id}"): SIGNED_IN,
    ("GET", "/entries/{entry_id}/evidence"): SIGNED_IN,
    ("POST", "/entries/{entry_id}/evidence"): SIGNED_IN,
    ("PATCH", "/evidence/{evidence_id}"): SIGNED_IN,
    ("DELETE", "/evidence/{evidence_id}"): SIGNED_IN,
    ("GET", "/evidence/{evidence_id}/content"): SIGNED_IN,
    # assessments: the item's assessor_position decides (AssessmentService)
    ("GET", "/assessments"): SIGNED_IN,
    ("GET", "/entries/{entry_id}/assessments"): SIGNED_IN,
    ("PUT", "/entries/{entry_id}/assessments/me"): SIGNED_IN,
    ("DELETE", "/entries/{entry_id}/assessments/me"): SIGNED_IN,
    # verification (005): reviewers, never on their own work (VerificationService)
    ("GET", "/publications/{publication_id}/verification"): SIGNED_IN,
    ("PUT", "/publications/{publication_id}/verification"): REVIEWERS,
    ("GET", "/evidence/{evidence_id}/verification"): SIGNED_IN,
    ("PUT", "/evidence/{evidence_id}/verification"): REVIEWERS,
    ("GET", "/verifications/publications"): REVIEWERS,
    ("GET", "/verifications/evidence"): REVIEWERS,
}


def rule_for(method: str, path: str) -> Rule | None:
    return ROUTE_RULES.get((method, path.removeprefix("/api/v2")))
