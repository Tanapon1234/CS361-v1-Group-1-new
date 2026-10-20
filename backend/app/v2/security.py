"""Who is calling: roles (docs/v2/permissions.md) and the caller object services receive."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    LECTURER = "lecturer"
    STAFF = "staff"
    REVIEWER = "reviewer"
    EXECUTIVE = "executive"
    ADMIN = "admin"


#: Roles that may see everyone's data (not change it)
VIEW_ALL_ROLES = frozenset({Role.STAFF, Role.REVIEWER, Role.EXECUTIVE, Role.ADMIN})


def roles_from_names(names: Iterable[str]) -> frozenset[Role]:
    """Cognito groups / X-Dev-Roles values that are roles; anything else is ignored."""
    known = {role.value for role in Role}
    return frozenset(Role(name.strip()) for name in names if name.strip() in known)


@dataclass(frozen=True, slots=True)
class Actor:
    """The caller. `lecturer_id` is None only for a dev-header script acting by role alone."""

    lecturer_id: UUID | None
    roles: frozenset[Role]

    def has_any(self, *roles: Role) -> bool:
        """Admin counts as every role."""
        return Role.ADMIN in self.roles or any(role in self.roles for role in roles)

    @property
    def views_all(self) -> bool:
        return self.has_any(*VIEW_ALL_ROLES)

    def is_lecturer(self, lecturer_id: UUID) -> bool:
        return self.lecturer_id is not None and self.lecturer_id == lecturer_id
