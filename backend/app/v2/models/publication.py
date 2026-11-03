import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk, pg_enum, timestamp_field, uuid_pk
from app.v2.models.enums import EvidenceStatus, VerificationStatus


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


class PublicationEvidence(SQLModel, table=True):
    """009_publication_evidence.sql: a supporting file for a publication that is not
    tied to any workload entry (FR4). No per-file verification; the publication's own
    verification_status (005) covers the whole publication."""

    __tablename__ = "publication_evidence"
    __table_args__ = (sa.Index(None, "publication_id"),)

    id: uuid.UUID = uuid_pk()
    publication_id: int = Field(sa_column_args=[fk("publication.publication_id")])
    label: str | None = Field(default=None, max_length=255)
    s3_key: str = Field(max_length=512, unique=True)
    file_name: str = Field(max_length=255)
    mime_type: str = Field(max_length=100)
    size_bytes: int = Field(sa_type=sa.BigInteger)
    checksum: str | None = Field(default=None, max_length=64)
    status: EvidenceStatus = Field(
        default=EvidenceStatus.PENDING, sa_type=pg_enum(EvidenceStatus, "evidence_status")
    )
    uploaded_by: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    created_at: datetime = timestamp_field()
