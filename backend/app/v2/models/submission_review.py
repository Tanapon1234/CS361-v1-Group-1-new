"""A reviewer's verdict on a whole sheet (014_submission_review.sql)."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, pg_enum, timestamp_field
from app.v2.models.enums import VerificationStatus


class SubmissionReview(SQLModel, table=True):
    __tablename__ = "submission_review"

    submission_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("submission.id")])
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        sa_type=pg_enum(VerificationStatus, "verification_status"),
    )
    note: str | None = Field(default=None)
    reviewed_by: uuid.UUID | None = Field(
        default=None, sa_column_args=[fk("lecturer.lecturer_id", cascade=False)]
    )
    reviewed_at: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))
    updated_at: datetime = timestamp_field(auto_update=True)
