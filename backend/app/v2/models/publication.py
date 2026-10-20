import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk, pg_enum, timestamp_field
from app.v2.models.enums import VerificationStatus


class Publication(SQLModel, table=True):
    __tablename__ = "publication"

    publication_id: int | None = identity_pk()
    title: str = Field(sa_type=sa.Text)
    publication_year: int | None = Field(default=None, sa_type=sa.SmallInteger)
    venue: str | None = Field(default=None, sa_type=sa.Text)
    volume: str | None = Field(default=None, max_length=50)
    pages: str | None = Field(default=None, max_length=50)
    doi: str | None = Field(default=None, max_length=255, unique=True)
    citation_text: str | None = Field(default=None, sa_type=sa.Text)
    created_at: datetime | None = timestamp_field()
    # 005_verification.sql: a reviewer's verdict
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        sa_type=pg_enum(VerificationStatus, "verification_status"),
        sa_column_kwargs={"server_default": "pending"},
    )
    verified_by: uuid.UUID | None = Field(
        default=None,
        sa_column_args=[
            sa.ForeignKey(
                "lecturer.lecturer_id",
                ondelete="SET NULL",
                deferrable=True,
                initially="IMMEDIATE",
            )
        ],
    )
    verified_at: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))
    verification_note: str | None = Field(default=None, sa_type=sa.Text)


class FacultyPublication(SQLModel, table=True):
    """Link table: authorship between lecturers and publications."""

    __tablename__ = "faculty_publication"

    lecturer_id: uuid.UUID = Field(primary_key=True, sa_column_args=[fk("lecturer.lecturer_id")])
    publication_id: int = Field(primary_key=True, sa_column_args=[fk("publication.publication_id")])
    author_order: int | None = Field(default=None, sa_type=sa.SmallInteger)
