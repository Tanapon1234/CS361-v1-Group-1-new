from app.v2.daos.audit_log_dao import AuditLogDAO
from app.v2.dtos.audit_log_dto import AuditLogQuery, AuditLogResponse
from app.v2.dtos.common import PageMeta, PageResponse


class AuditLogService:
    def __init__(self, audit_log_dao: AuditLogDAO) -> None:
        self.audit_log_dao = audit_log_dao

    def list_audit_log(self, query: AuditLogQuery) -> PageResponse[AuditLogResponse]:
        items, total = self.audit_log_dao.find_page(
            entity=query.entity,
            entity_id=query.entity_id,
            actor_id=query.actor_id,
            limit=query.limit,
            offset=query.offset,
        )
        return PageResponse(
            items=[AuditLogResponse.model_validate(item) for item in items],
            meta=PageMeta(total=total, limit=query.limit, offset=query.offset),
        )
