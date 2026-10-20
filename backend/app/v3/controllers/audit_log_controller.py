"""Who changed what, and when (admin only)."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.v3.dependencies import AuditLogServiceDep
from app.v3.dtos.audit_log_dto import AuditLogQuery, AuditLogResponse
from app.v3.dtos.common import PageResponse

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("")
def list_audit_log(
    query: Annotated[AuditLogQuery, Query()], service: AuditLogServiceDep
) -> PageResponse[AuditLogResponse]:
    """Newest first; filter by `entity` (table), `entity_id` and `actor_id`."""
    return service.list_audit_log(query)
