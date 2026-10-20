from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.v2.dtos.base import ResponseDTO
from app.v2.dtos.common import PageQuery


class AuditLogQuery(PageQuery):
    entity: str | None = Field(default=None, max_length=50, examples=["publication"])
    entity_id: str | None = Field(default=None, max_length=100)
    actor_id: UUID | None = None


class AuditLogResponse(ResponseDTO):
    id: int
    occurred_at: datetime
    actor_id: UUID | None
    actor_roles: str
    request: str | None
    action: str
    entity: str
    entity_id: str
    # insert / delete: the row's values; update: {column: [old, new]}
    changes: dict[str, Any] | None
