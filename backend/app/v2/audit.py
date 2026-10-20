"""Write one audit_log row (006) for every row the API inserts, updates or deletes.

`authorize` (dependencies.py) puts the caller on the request's session (`session.info`);
the after_flush hook below turns the flushed changes into audit rows in the same
transaction, so a rolled-back change leaves no trace either. Sessions without a caller
(tests, scripts using the ORM directly) are not audited.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import event, insert, inspect
from sqlmodel import Session, SQLModel

from app.v2.models.audit_log import AuditLog
from app.v2.security import Actor

_ACTOR = "audit_actor"
_REQUEST = "audit_request"


def attach(session: Session, actor: Actor, request: str) -> None:
    session.info[_ACTOR] = actor
    session.info[_REQUEST] = request[:300]


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID | Decimal | datetime | date):
        return str(value)
    return value


def _values(obj: SQLModel) -> dict[str, Any]:
    return {
        column.key: _plain(getattr(obj, column.key)) for column in inspect(obj).mapper.column_attrs
    }


def _changed(obj: SQLModel) -> dict[str, list[Any]]:
    """{column: [old, new]} of the columns this flush changed."""
    changes = {}
    for attr in inspect(obj).attrs:
        history = attr.history
        if history.has_changes():
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            changes[attr.key] = [_plain(old), _plain(new)]
    return changes


def _entity_id(obj: SQLModel) -> str:
    """Primary key (joined with "," for link tables); set by the flush for new rows."""
    state = inspect(obj)
    return ",".join(str(part) for part in state.mapper.primary_key_from_instance(obj))


@event.listens_for(Session, "after_flush")
def _write_audit_rows(session: Session, _flush_context: Any) -> None:
    actor: Actor | None = session.info.get(_ACTOR)
    if actor is None:
        return
    rows = []
    for action, objects in (
        ("insert", session.new),
        ("update", session.dirty),
        ("delete", session.deleted),
    ):
        for obj in objects:
            if isinstance(obj, AuditLog) or not isinstance(obj, SQLModel):
                continue
            if action == "update":
                changes = _changed(obj)
                if not changes:
                    continue
            else:
                changes = _values(obj)
            rows.append(
                {
                    "actor_id": actor.lecturer_id,
                    "actor_roles": ",".join(sorted(actor.roles)),
                    "request": session.info.get(_REQUEST),
                    "action": action,
                    "entity": obj.__tablename__,
                    "entity_id": _entity_id(obj),
                    # Round-trip through JSON so every value is storable in jsonb
                    "changes": json.loads(json.dumps(changes, default=str)),
                }
            )
    if rows:
        session.connection().execute(insert(AuditLog.__table__), rows)
