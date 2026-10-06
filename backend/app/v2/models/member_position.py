import uuid
from datetime import date

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, pg_enum, uuid_pk
from app.v2.models.enums import PositionCode


class MemberPosition(SQLModel, table=True):
    """An administrative position a lecturer holds (also who may assess workload items)."""

    __tablename__ = "member_position"
    __table_args__ = (
        sa.Index(None, "lecturer_id", "start_date"),
        sa.Index(None, "position", "department_id"),
    )

    id: uuid.UUID = uuid_pk()
    lecturer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    position: PositionCode = Field(sa_type=pg_enum(PositionCode, "position_code"))
    # NULL = faculty-level position (dean, executive committee)
    department_id: int | None = Field(
        default=None, sa_type=sa.SmallInteger, sa_column_args=[fk("department.id", cascade=False)]
    )
    start_date: date
    # NULL = still holds the position
    end_date: date | None = None
