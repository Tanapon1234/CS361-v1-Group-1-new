"""Roles an admin grants from the app (013_user_role.sql)."""

from datetime import datetime
from uuid import UUID

from app.v3.dtos.base import QueryDTO, RequestDTO, ResponseDTO
from app.v3.security import Role


class UserRoleListQuery(QueryDTO):
    lecturer_id: UUID | None = None


class UserRoleGrantRequest(RequestDTO):
    lecturer_id: UUID
    role: Role


class UserRoleResponse(ResponseDTO):
    lecturer_id: UUID
    lecturer_name_th: str
    role: Role
    granted_by: UUID
    created_at: datetime
