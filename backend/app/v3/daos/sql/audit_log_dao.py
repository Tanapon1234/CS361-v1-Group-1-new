from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select

from app.v2.models.audit_log import AuditLog
from app.v3.daos.audit_log_dao import AuditLogDAO
from app.v3.daos.sql.base import SqlDAO


class SqlAuditLogDAO(SqlDAO, AuditLogDAO):
    def find_page(
        self,
        *,
        entity: str | None,
        entity_id: str | None,
        actor_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[AuditLog], int]:
        statement = select(AuditLog)
        if entity is not None:
            statement = statement.where(AuditLog.entity == entity)
        if entity_id is not None:
            statement = statement.where(AuditLog.entity_id == entity_id)
        if actor_id is not None:
            statement = statement.where(AuditLog.actor_id == actor_id)
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = self.session.exec(
            statement.order_by(col(AuditLog.id).desc()).offset(offset).limit(limit)
        ).all()
        return items, total
