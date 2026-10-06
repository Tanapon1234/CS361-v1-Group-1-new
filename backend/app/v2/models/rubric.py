"""Workload rubric (versioned): version -> category -> section -> item."""

from datetime import date
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.v2.models.base import fk, identity_pk, pg_enum
from app.v2.models.enums import (
    AssessmentAgg,
    PositionCode,
    QuantityUnit,
    RangeBasis,
    WeightMode,
)


class RubricVersion(SQLModel, table=True):
    __tablename__ = "rubric_version"

    id: int | None = identity_pk(sa.SmallInteger)
    code: str = Field(max_length=30, unique=True)
    approved_meeting: str | None = Field(default=None, max_length=50)
    approved_on: date | None = None
    base_points: Decimal = Field(default=Decimal(200), sa_type=sa.Numeric(6, 2))
    overall_cap: Decimal = Field(default=Decimal(2000), sa_type=sa.Numeric(8, 2))
    min_required: Decimal = Field(default=Decimal(650), sa_type=sa.Numeric(8, 2))
    min_teaching_credits: Decimal = Field(default=Decimal(6), sa_type=sa.Numeric(5, 2))
    is_active: bool = True


class RubricCategory(SQLModel, table=True):
    __tablename__ = "rubric_category"
    __table_args__ = (sa.Index(None, "version_id", "code", unique=True),)

    id: int | None = identity_pk(sa.SmallInteger)
    version_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("rubric_version.id", cascade=False)]
    )
    code: str = Field(max_length=5)
    name_th: str = Field(max_length=100)
    cap: Decimal = Field(sa_type=sa.Numeric(8, 2))
    sort_order: int = Field(sa_type=sa.SmallInteger)


class RubricSection(SQLModel, table=True):
    __tablename__ = "rubric_section"
    __table_args__ = (sa.Index(None, "category_id", "code", unique=True),)

    id: int | None = identity_pk(sa.SmallInteger)
    category_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("rubric_category.id", cascade=False)]
    )
    parent_id: int | None = Field(
        default=None,
        sa_type=sa.SmallInteger,
        sa_column_args=[fk("rubric_section.id", cascade=False)],
    )
    code: str = Field(max_length=10)
    name_th: str = Field(max_length=255)
    cap: Decimal | None = Field(default=None, sa_type=sa.Numeric(8, 2))
    max_entries: int | None = Field(default=None, sa_type=sa.SmallInteger)
    sort_order: int = Field(sa_type=sa.SmallInteger)


class RubricItem(SQLModel, table=True):
    __tablename__ = "rubric_item"

    id: int | None = identity_pk(sa.SmallInteger)
    section_id: int = Field(
        sa_type=sa.SmallInteger, sa_column_args=[fk("rubric_section.id", cascade=False)]
    )
    label_th: str = Field(max_length=255)
    weight_mode: WeightMode = Field(
        default=WeightMode.FIXED, sa_type=pg_enum(WeightMode, "weight_mode")
    )
    weight: Decimal | None = Field(default=None, sa_type=sa.Numeric(6, 4))
    weight_min: Decimal | None = Field(default=None, sa_type=sa.Numeric(8, 4))
    weight_max: Decimal | None = Field(default=None, sa_type=sa.Numeric(8, 4))
    range_basis: RangeBasis | None = Field(default=None, sa_type=pg_enum(RangeBasis, "range_basis"))
    assessor_position: PositionCode | None = Field(
        default=None, sa_type=pg_enum(PositionCode, "position_code")
    )
    assessment_agg: AssessmentAgg = Field(
        default=AssessmentAgg.NONE, sa_type=pg_enum(AssessmentAgg, "assessment_agg")
    )
    unit: QuantityUnit = Field(sa_type=pg_enum(QuantityUnit, "quantity_unit"))
    unit_divisor: Decimal = Field(default=Decimal(1), sa_type=sa.Numeric(6, 2))
    uses_participation: bool = False
    counts_teaching_credit: bool = False
    once_per_round: bool = False
    tier_min: int | None = None
    tier_max: int | None = None
    field_schema: dict[str, Any] | None = Field(default=None, sa_type=JSONB)
    is_active: bool = True
