"""Evaluation rounds and each lecturer's workload submission (ใบภาระงาน) for a round."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk, pg_enum, timestamp_field, uuid_pk
from app.v2.models.enums import (
    AcademicRank,
    ApprovalDecision,
    DataSource,
    EvidenceStatus,
    PositionCode,
    SignerRole,
    SubmissionStatus,
)


class EvaluationRound(SQLModel, table=True):
    __tablename__ = "evaluation_round"

    id: int | None = identity_pk(sa.SmallInteger)
    rubric_version_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("rubric_version.id", cascade=False)]
    )
    name_th: str = Field(max_length=100)
    period_start: date
    period_end: date
    salary_effective_on: date
    academic_year: int = Field(sa_type=sa.SmallInteger)
    semester: int | None = Field(default=None, sa_type=sa.SmallInteger)
    submit_due_at: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))
    is_open: bool = False


class Submission(SQLModel, table=True):
    __tablename__ = "submission"
    __table_args__ = (
        sa.Index(None, "round_id", "lecturer_id", unique=True),
        sa.Index(None, "round_id", "status"),
    )

    id: uuid.UUID = uuid_pk()
    round_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("evaluation_round.id", cascade=False)]
    )
    lecturer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    status: SubmissionStatus = Field(
        default=SubmissionStatus.DRAFT, sa_type=pg_enum(SubmissionStatus, "submission_status")
    )
    rank_snapshot: AcademicRank = Field(sa_type=pg_enum(AcademicRank, "academic_rank"))
    department_snapshot: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("department.id", cascade=False)]
    )
    teaching_credits: Decimal = Field(default=Decimal(0), sa_type=sa.Numeric(6, 2))
    raw_total: Decimal = Field(default=Decimal(0), sa_type=sa.Numeric(8, 2))
    capped_total: Decimal = Field(default=Decimal(0), sa_type=sa.Numeric(8, 2))
    submitted_at: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field(auto_update=True)


class SubmissionEntry(SQLModel, table=True):
    """One line on a submission. The DB rejects changes once the submission is not a draft."""

    __tablename__ = "submission_entry"
    __table_args__ = (
        sa.Index(None, "submission_id", "item_id"),
        sa.Index(None, "course_code", "section_no"),
    )

    id: uuid.UUID = uuid_pk()
    submission_id: uuid.UUID = Field(sa_column_args=[fk("submission.id")])
    item_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("rubric_item.id", cascade=False)]
    )
    title: str | None = Field(default=None, max_length=500)
    course_code: str | None = Field(default=None, max_length=15)
    section_no: str | None = Field(default=None, max_length=10)
    student_count: int | None = None
    data_source: DataSource = Field(
        default=DataSource.MANUAL, sa_type=pg_enum(DataSource, "data_source")
    )
    synced_at: datetime | None = Field(default=None, sa_type=sa.DateTime(timezone=True))
    quantity: Decimal = Field(default=Decimal(1), sa_type=sa.Numeric(8, 2))
    participation_pct: Decimal = Field(default=Decimal(100), sa_type=sa.Numeric(5, 2))
    weight_applied: Decimal | None = Field(default=None, sa_type=sa.Numeric(8, 4))
    credits: Decimal | None = Field(default=None, sa_type=sa.Numeric(5, 2))
    score: Decimal = Field(default=Decimal(0), sa_type=sa.Numeric(8, 2))
    details: dict[str, Any] | None = Field(default=None, sa_type=JSONB)
    note: str | None = Field(default=None, sa_type=sa.Text)
    sort_order: int = Field(default=0, sa_type=sa.SmallInteger)
    created_at: datetime = timestamp_field()
    updated_at: datetime = timestamp_field(auto_update=True)


class EntryAssessment(SQLModel, table=True):
    """The value one assessor gives to an entry (one value per assessor per entry)."""

    __tablename__ = "entry_assessment"
    __table_args__ = (sa.Index(None, "entry_id", "assessor_id", unique=True),)

    id: uuid.UUID = uuid_pk()
    entry_id: uuid.UUID = Field(sa_column_args=[fk("submission_entry.id")])
    assessor_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    position_used: PositionCode = Field(sa_type=pg_enum(PositionCode, "position_code"))
    value_given: Decimal = Field(sa_type=sa.Numeric(8, 4))
    comment: str | None = Field(default=None, sa_type=sa.Text)
    assessed_at: datetime = timestamp_field()


class EntryEvidence(SQLModel, table=True):
    """An evidence file in S3 attached to an entry."""

    __tablename__ = "entry_evidence"
    __table_args__ = (sa.Index(None, "entry_id"), sa.Index(None, "status"))

    id: uuid.UUID = uuid_pk()
    entry_id: uuid.UUID = Field(sa_column_args=[fk("submission_entry.id")])
    ref_code: str | None = Field(default=None, max_length=50)
    label: str | None = Field(default=None, max_length=255)
    s3_key: str = Field(max_length=512, unique=True)
    file_name: str = Field(max_length=255)
    mime_type: str = Field(max_length=100)
    size_bytes: int = Field(sa_type=sa.BigInteger)
    checksum: str | None = Field(default=None, sa_type=sa.CHAR(64))
    status: EvidenceStatus = Field(
        default=EvidenceStatus.PENDING, sa_type=pg_enum(EvidenceStatus, "evidence_status")
    )
    uploaded_by: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    created_at: datetime = timestamp_field()


class SubmissionCategoryTotal(SQLModel, table=True):
    """Category totals frozen when a submission is sent."""

    __tablename__ = "submission_category_total"

    submission_id: uuid.UUID = Field(
        primary_key=True, sa_column_args=[fk("submission.id", cascade=False)]
    )
    category_id: int = Field(
        primary_key=True,
        sa_type=sa.SmallInteger,
        sa_column_args=[fk("rubric_category.id", cascade=False)],
    )
    raw_score: Decimal = Field(sa_type=sa.Numeric(8, 2))
    capped_score: Decimal = Field(sa_type=sa.Numeric(8, 2))


class SubmissionApproval(SQLModel, table=True):
    """One step in a submission's history: sent, received, returned or approved."""

    __tablename__ = "submission_approval"
    __table_args__ = (sa.Index(None, "submission_id", "signed_at"),)

    id: uuid.UUID = uuid_pk()
    submission_id: uuid.UUID = Field(sa_column_args=[fk("submission.id", cascade=False)])
    signer_id: uuid.UUID = Field(sa_column_args=[fk("lecturer.lecturer_id", cascade=False)])
    role: SignerRole = Field(sa_type=pg_enum(SignerRole, "signer_role"))
    decision: ApprovalDecision = Field(sa_type=pg_enum(ApprovalDecision, "approval_decision"))
    comment: str | None = Field(default=None, sa_type=sa.Text)
    signed_at: datetime = timestamp_field()
