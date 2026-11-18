"""Roles an admin grants from the app. Staff and admin are granted here. The others are not:
executive is the department head (derived from the dept_chair position), reviewer is derived
from an active reviewer_assignment, and lecturer is implicit. A leftover executive row from
before that rule can still be revoked. Grants and revokes are audited with every other
change (audit.py).
"""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.v2.models.user_role import UserRole
from app.v3.daos.lecturer_dao import LecturerDAO
from app.v3.daos.user_role_dao import UserRoleDAO
from app.v3.dtos.common import ListMeta, ListResponse
from app.v3.dtos.user_role_dto import UserRoleGrantRequest, UserRoleListQuery, UserRoleResponse
from app.v3.security import GRANTABLE_ROLES, Actor, Role
from app.v3.services.db_errors import is_unique_violation


class UserRoleService:
    def __init__(self, user_role_dao: UserRoleDAO, lecturer_dao: LecturerDAO) -> None:
        self.user_role_dao = user_role_dao
        self.lecturer_dao = lecturer_dao

    def list_roles(self, query: UserRoleListQuery) -> ListResponse[UserRoleResponse]:
        rows = self.user_role_dao.list_all(lecturer_id=query.lecturer_id)
        items = [self._to_response(row) for row in rows]
        return ListResponse(items=items, meta=ListMeta(count=len(items)))

    def grant(self, actor: Actor, data: UserRoleGrantRequest) -> UserRoleResponse:
        if actor.lecturer_id is None:
            raise ForbiddenError("Sign in as a person: a grant records who made it")
        self._require_grantable(data.role)
        if self.lecturer_dao.get_by_id(data.lecturer_id) is None:
            raise NotFoundError("Lecturer not found")
        try:
            row = self.user_role_dao.add(
                UserRole(
                    lecturer_id=data.lecturer_id,
                    role=data.role.value,
                    granted_by=actor.lecturer_id,
                )
            )
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise ConflictError("This lecturer already has this role") from exc
            raise
        return self._to_response(row)

    def revoke(self, actor: Actor, lecturer_id: UUID, role: Role) -> None:
        if role not in GRANTABLE_ROLES | {Role.EXECUTIVE}:
            raise BadRequestError("Only a role stored in user_role can be revoked here")
        row = self.user_role_dao.get(lecturer_id, role.value)
        if row is None:
            raise NotFoundError("This lecturer does not have this role")
        if role is Role.ADMIN:
            if actor.is_lecturer(lecturer_id):
                raise ConflictError("You cannot revoke your own admin role")
            if self.user_role_dao.count_with_role(Role.ADMIN.value) <= 1:
                raise ConflictError("You cannot revoke the last admin")
        self.user_role_dao.delete(row)

    # --- helpers ------------------------------------------------------------------

    @staticmethod
    def _require_grantable(role: Role) -> None:
        if role not in GRANTABLE_ROLES:
            raise BadRequestError(
                "Only staff and admin are granted here: executive is whoever holds the "
                "department head position, reviewer comes from a reviewer assignment, "
                "and lecturer is implicit"
            )

    def _to_response(self, row: UserRole) -> UserRoleResponse:
        lecturer = self.lecturer_dao.get_by_id(row.lecturer_id)
        return UserRoleResponse(
            lecturer_id=row.lecturer_id,
            lecturer_name_th=lecturer.name_th if lecturer else "",
            role=Role(row.role),
            granted_by=row.granted_by,
            created_at=row.created_at,
        )
