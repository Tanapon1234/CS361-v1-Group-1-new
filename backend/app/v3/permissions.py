"""Who may call which /api/v3 endpoint: docs/v2/permissions.md as code.

The api_v2 router checks every request against ROUTE_RULES before the controller runs.
A route with no rule is refused, and tests/v2/test_permissions.py fails until it has one.
Rules decide from the caller alone (roles, positions, `lecturer_id` in the path); checks
that need data (owner of a submission, authors of a publication, department of a
lecturer) are in the services, see app/v3/services/access.py.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.v2.models.enums import PositionCode
from app.v3.security import VIEW_ALL_ROLES, Actor, Role

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
REVIEWERS = Rule(roles=frozenset({Role.REVIEWER}))
ADMIN = Rule(roles=frozenset({Role.ADMIN}))
# STAFF has no master-data create/edit rights (view-only, department-scoped in services);
# that leaves only admin, or the lecturer acting on their own record
SELF_OR_ADMIN = Rule(self_param="lecturer_id")
# See everyone's data; department signers too, but services narrow them to their department
VIEWERS = Rule(roles=VIEW_ALL_ROLES, positions=DEPARTMENT_SIGNERS)
SELF_OR_VIEWERS = Rule(roles=VIEW_ALL_ROLES, positions=DEPARTMENT_SIGNERS, self_param="lecturer_id")

# (method, path without the /api/v3 prefix) -> rule
ROUTE_RULES: dict[tuple[str, str], Rule] = {
    # lecturer
    ("GET", "/lecturers"): SIGNED_IN,
    ("POST", "/lecturers"): ADMIN,
    ("GET", "/lecturers/{lecturer_id}"): SIGNED_IN,
    # self may edit contact fields only (LecturerService.update_lecturer)
    ("PATCH", "/lecturers/{lecturer_id}"): SELF_OR_ADMIN,
    ("POST", "/lecturers/{lecturer_id}/activate"): ADMIN,
    ("POST", "/lecturers/{lecturer_id}/deactivate"): ADMIN,
    # profile image / cv
    ("GET", "/lecturers/{lecturer_id}/profile-image"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/profile-image/presign"): SELF_OR_ADMIN,
    ("POST", "/lecturers/{lecturer_id}/profile-image/complete"): SELF_OR_ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/profile-image"): SELF_OR_ADMIN,
    ("GET", "/lecturers/{lecturer_id}/cv"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/cv/presign"): SELF_OR_ADMIN,
    ("POST", "/lecturers/{lecturer_id}/cv/complete"): SELF_OR_ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/cv"): SELF_OR_ADMIN,
    # education
    ("GET", "/lecturers/{lecturer_id}/educations"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/educations"): SELF_OR_ADMIN,
    ("PATCH", "/lecturers/{lecturer_id}/educations/{education_id}"): SELF_OR_ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/educations/{education_id}"): SELF_OR_ADMIN,
    # research interests: anyone may add a topic to the master list
    ("GET", "/research-interests"): SIGNED_IN,
    ("POST", "/research-interests"): SIGNED_IN,
    ("PATCH", "/research-interests/{research_interest_id}"): ADMIN,
    ("DELETE", "/research-interests/{research_interest_id}"): ADMIN,
    ("GET", "/lecturers/{lecturer_id}/research-interests"): SIGNED_IN,
    ("PUT", "/lecturers/{lecturer_id}/research-interests"): SELF_OR_ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/research-interests/{research_interest_id}"): SELF_OR_ADMIN,
    # publication profiles
    ("GET", "/lecturers/{lecturer_id}/publication-profiles"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/publication-profiles"): SELF_OR_ADMIN,
    (
        "PATCH",
        "/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}",
    ): SELF_OR_ADMIN,
    (
        "DELETE",
        "/lecturers/{lecturer_id}/publication-profiles/{publication_profile_id}",
    ): SELF_OR_ADMIN,
    # publications: authors or staff edit (PublicationService)
    ("GET", "/publications"): SIGNED_IN,
    ("POST", "/publications"): SIGNED_IN,
    ("GET", "/publications/{publication_id}"): SIGNED_IN,
    ("PATCH", "/publications/{publication_id}"): SIGNED_IN,
    ("DELETE", "/publications/{publication_id}"): SIGNED_IN,
    # publication evidence (V4 FR4): author or staff edit (PublicationEvidenceService),
    # same visibility as the publication itself
    ("GET", "/publications/{publication_id}/evidence"): SIGNED_IN,
    ("POST", "/publications/{publication_id}/evidence"): SIGNED_IN,
    ("PATCH", "/publications/{publication_id}/evidence/{evidence_id}"): SIGNED_IN,
    ("DELETE", "/publications/{publication_id}/evidence/{evidence_id}"): SIGNED_IN,
    ("GET", "/publications/{publication_id}/evidence/{evidence_id}/content"): SIGNED_IN,
    ("GET", "/lecturers/{lecturer_id}/publications"): SIGNED_IN,
    # expertise
    ("GET", "/expertise"): SIGNED_IN,
    ("POST", "/expertise"): SIGNED_IN,
    ("GET", "/expertise/{expertise_id}"): SIGNED_IN,
    ("PATCH", "/expertise/{expertise_id}"): ADMIN,
    ("DELETE", "/expertise/{expertise_id}"): ADMIN,
    ("GET", "/lecturers/{lecturer_id}/expertise"): SIGNED_IN,
    ("PUT", "/lecturers/{lecturer_id}/expertise"): SELF_OR_ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/expertise/{expertise_id}"): SELF_OR_ADMIN,
    # a lecturer's work by year: department signers only for their department (service)
    ("GET", "/lecturers/{lecturer_id}/work"): SELF_OR_VIEWERS,
    # --- workload ---
    ("GET", "/me"): SIGNED_IN,
    ("GET", "/departments"): SIGNED_IN,
    ("POST", "/departments"): ADMIN,
    ("PATCH", "/departments/{department_id}"): ADMIN,
    # staff/reviewer narrowed to their own department in the service (access.py); not a
    # plain-lecturer endpoint (V4 FR8: staff/executive summary, not self-service)
    ("GET", "/departments/{department_id}/report"): VIEWERS,
    ("GET", "/lecturers/{lecturer_id}/positions"): SIGNED_IN,
    ("POST", "/lecturers/{lecturer_id}/positions"): ADMIN,
    ("PATCH", "/lecturers/{lecturer_id}/positions/{position_id}"): ADMIN,
    ("DELETE", "/lecturers/{lecturer_id}/positions/{position_id}"): ADMIN,
    # rubric
    ("GET", "/rubric-versions"): SIGNED_IN,
    ("POST", "/rubric-versions"): ADMIN,
    ("GET", "/rubric-versions/{version_id}"): SIGNED_IN,
    ("PATCH", "/rubric-versions/{version_id}"): ADMIN,
    ("GET", "/rubric-versions/{version_id}/form"): SIGNED_IN,
    ("GET", "/rubric-versions/{version_id}/categories"): SIGNED_IN,
    ("POST", "/rubric-versions/{version_id}/categories"): ADMIN,
    ("GET", "/rubric-categories/{category_id}/sections"): SIGNED_IN,
    ("POST", "/rubric-categories/{category_id}/sections"): ADMIN,
    ("PATCH", "/rubric-sections/{section_id}"): ADMIN,
    ("DELETE", "/rubric-sections/{section_id}"): ADMIN,
    ("GET", "/rubric-sections/{section_id}/items"): SIGNED_IN,
    ("POST", "/rubric-sections/{section_id}/items"): ADMIN,
    ("PATCH", "/rubric-items/{item_id}"): ADMIN,
    ("DELETE", "/rubric-items/{item_id}"): ADMIN,
    # rounds
    ("GET", "/rounds"): SIGNED_IN,
    ("POST", "/rounds"): ADMIN,
    ("GET", "/rounds/{round_id}"): SIGNED_IN,
    ("PATCH", "/rounds/{round_id}"): ADMIN,
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
    # V4 #292: only the owner confirms a staff-drafted entry (EntryService.confirm_entry)
    ("POST", "/entries/{entry_id}/confirm"): SIGNED_IN,
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
    # audit log (006)
    ("GET", "/audit-log"): ADMIN,
}


def rule_for(method: str, path: str) -> Rule | None:
    return ROUTE_RULES.get((method, path.removeprefix("/api/v3")))
