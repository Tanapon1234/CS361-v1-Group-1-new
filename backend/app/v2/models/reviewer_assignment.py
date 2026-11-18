"""Who reviews whom (011/012_reviewer_assignment*.sql, V4 #293)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, timestamp_field, uuid_pk


class ReviewerAssignment(SQLModel, table=True):
    __tablename__ = "reviewer_assignment"
    __table_args__ = (sa.UniqueConstraint("round_id", "reviewer_id", "reviewee_id"),)

    id: uuid.UUID = uuid_pk()
    round_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("evaluation_round.id", cascade=False)]
    )
    reviewer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    reviewee_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    assigned_by: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    created_at: datetime = timestamp_field()
