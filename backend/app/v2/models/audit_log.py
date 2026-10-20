import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.v2.models.base import identity_pk, timestamp_field


class AuditLog(SQLModel, table=True):
    """One inserted / updated / deleted row (006). Written by app/v2/audit.py only."""

    __tablename__ = "audit_log"
    __table_args__ = (
        sa.CheckConstraint("action IN ('insert', 'update', 'delete')", name="chk_audit_log_action"),
        sa.Index(None, "entity", "entity_id"),
        sa.Index(None, "actor_id"),
        sa.Index(None, "occurred_at"),
    )

    id: int | None = identity_pk(sa.BigInteger)
    occurred_at: datetime = timestamp_field()
    # No foreign key: the history stays even if the lecturer is deleted later
    actor_id: uuid.UUID | None = None
    actor_roles: str = Field(default="", max_length=100)
    request: str | None = Field(default=None, max_length=300)
    action: str = Field(max_length=10)
    entity: str = Field(max_length=50)
    entity_id: str = Field(max_length=100)
    changes: dict[str, Any] | None = Field(default=None, sa_type=JSONB)
