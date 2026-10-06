from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.v2.dtos.base import RequestDTO, ResponseDTO
from app.v2.dtos.common import Number
from app.v2.models.enums import (
    AssessmentAgg,
    PositionCode,
    QuantityUnit,
    RangeBasis,
    WeightMode,
)

# --- version ----------------------------------------------------------------------


class RubricVersionCreateRequest(RequestDTO):
    code: str = Field(min_length=1, max_length=30, examples=["2567-r1"])
    approved_meeting: str | None = Field(default=None, max_length=50)
    approved_on: date | None = None
    base_points: Decimal = Field(default=Decimal(200), gt=0, max_digits=6, decimal_places=2)
    overall_cap: Decimal = Field(default=Decimal(2000), gt=0, max_digits=8, decimal_places=2)
    min_required: Decimal = Field(default=Decimal(650), ge=0, max_digits=8, decimal_places=2)
    min_teaching_credits: Decimal = Field(default=Decimal(6), ge=0, max_digits=5, decimal_places=2)
    is_active: bool = True
    # Copy every category, section and item from this version
    source_version_id: int | None = Field(default=None, ge=1, le=32767)


class RubricVersionUpdateRequest(RequestDTO):
    code: str | None = Field(default=None, min_length=1, max_length=30)
    approved_meeting: str | None = Field(default=None, max_length=50)
    approved_on: date | None = None
    base_points: Decimal | None = Field(default=None, gt=0, max_digits=6, decimal_places=2)
    overall_cap: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    min_required: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    min_teaching_credits: Decimal | None = Field(default=None, ge=0, max_digits=5, decimal_places=2)
    is_active: bool | None = None

    @field_validator(
        "code", "base_points", "overall_cap", "min_required", "min_teaching_credits", "is_active"
    )
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class RubricVersionResponse(ResponseDTO):
    id: int
    code: str
    approved_meeting: str | None
    approved_on: date | None
    base_points: Number
    overall_cap: Number
    min_required: Number
    min_teaching_credits: Number
    is_active: bool


# --- category ---------------------------------------------------------------------


class RubricCategoryCreateRequest(RequestDTO):
    code: str = Field(min_length=1, max_length=5, examples=["1"])
    name_th: str = Field(min_length=1, max_length=100, examples=["งานสอน"])
    cap: Decimal = Field(ge=0, max_digits=8, decimal_places=2, examples=[900])
    sort_order: int = Field(ge=0, le=32767)


class RubricCategoryResponse(ResponseDTO):
    id: int
    version_id: int
    code: str
    name_th: str
    cap: Number
    sort_order: int


# --- section ----------------------------------------------------------------------


class RubricSectionCreateRequest(RequestDTO):
    code: str = Field(min_length=1, max_length=10, examples=["2.3.1"])
    name_th: str = Field(min_length=1, max_length=255)
    # A parent section in the same category (e.g. 2.3 -> 2.3.1)
    parent_id: int | None = Field(default=None, ge=1, le=32767)
    cap: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    max_entries: int | None = Field(default=None, ge=1, le=32767)
    sort_order: int = Field(ge=0, le=32767)


class RubricSectionUpdateRequest(RequestDTO):
    code: str | None = Field(default=None, min_length=1, max_length=10)
    name_th: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: int | None = Field(default=None, ge=1, le=32767)
    cap: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    max_entries: int | None = Field(default=None, ge=1, le=32767)
    sort_order: int | None = Field(default=None, ge=0, le=32767)

    @field_validator("code", "name_th", "sort_order")
    @classmethod
    def must_not_be_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field must not be null")
        return value


class RubricSectionResponse(ResponseDTO):
    id: int
    category_id: int
    parent_id: int | None
    code: str
    name_th: str
    cap: Number | None
    max_entries: int | None
    sort_order: int


# --- item -------------------------------------------------------------------------


class FieldSpec(BaseModel):
    """One extra field of an item, e.g. `{"quartile": {"type": "enum", "values": [...]}}`."""

    type: Literal["int", "number", "money", "string", "enum", "date", "bool"]
    required: bool = False
    values: list[str] | None = None

    @model_validator(mode="after")
    def enum_needs_values(self) -> Self:
        if self.type == "enum" and not self.values:
            raise ValueError("an enum field needs `values`")
        return self


class RubricItemFields(RequestDTO):
    """Every column of an item, with the rules that tie them together."""

    label_th: str = Field(min_length=1, max_length=255)
    weight_mode: WeightMode = WeightMode.FIXED
    weight: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=4)
    weight_min: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=4)
    weight_max: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=4)
    range_basis: RangeBasis | None = None
    assessor_position: PositionCode | None = None
    assessment_agg: AssessmentAgg = AssessmentAgg.NONE
    unit: QuantityUnit
    unit_divisor: Decimal = Field(default=Decimal(1), gt=0, max_digits=6, decimal_places=2)
    uses_participation: bool = False
    counts_teaching_credit: bool = False
    once_per_round: bool = False
    tier_min: int | None = Field(default=None, ge=0)
    tier_max: int | None = Field(default=None, ge=0)
    field_schema: dict[str, FieldSpec] | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def mode_fields_are_consistent(self) -> Self:
        if self.weight_mode is WeightMode.FIXED:
            if self.weight is None:
                raise ValueError("a fixed item needs `weight`")
        else:
            if self.weight_min is None or self.weight_max is None:
                raise ValueError("a ranged item needs `weight_min` and `weight_max`")
            if self.weight_min > self.weight_max:
                raise ValueError("weight_min must be <= weight_max")
            if self.range_basis is None or self.assessor_position is None:
                raise ValueError("a ranged item needs `range_basis` and `assessor_position`")
            if self.assessment_agg is AssessmentAgg.NONE:
                raise ValueError("a ranged item needs `assessment_agg` single or average")
        if (
            self.tier_min is not None
            and self.tier_max is not None
            and self.tier_min > self.tier_max
        ):
            raise ValueError("tier_min must be <= tier_max")
        return self


class RubricItemCreateRequest(RubricItemFields):
    pass


class RubricItemUpdateRequest(RequestDTO):
    """Only sent fields change; the result is checked with the same rules as create."""

    label_th: str | None = Field(default=None, min_length=1, max_length=255)
    weight_mode: WeightMode | None = None
    weight: Decimal | None = Field(default=None, ge=0, max_digits=6, decimal_places=4)
    weight_min: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=4)
    weight_max: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=4)
    range_basis: RangeBasis | None = None
    assessor_position: PositionCode | None = None
    assessment_agg: AssessmentAgg | None = None
    unit: QuantityUnit | None = None
    unit_divisor: Decimal | None = Field(default=None, gt=0, max_digits=6, decimal_places=2)
    uses_participation: bool | None = None
    counts_teaching_credit: bool | None = None
    once_per_round: bool | None = None
    tier_min: int | None = Field(default=None, ge=0)
    tier_max: int | None = Field(default=None, ge=0)
    field_schema: dict[str, FieldSpec] | None = None
    is_active: bool | None = None


class RubricItemResponse(ResponseDTO):
    id: int
    section_id: int
    label_th: str
    weight_mode: WeightMode
    weight: Number | None
    weight_min: Number | None
    weight_max: Number | None
    range_basis: RangeBasis | None
    assessor_position: PositionCode | None
    assessment_agg: AssessmentAgg
    unit: QuantityUnit
    unit_divisor: Number
    uses_participation: bool
    counts_teaching_credit: bool
    once_per_round: bool
    tier_min: int | None
    tier_max: int | None
    field_schema: dict[str, FieldSpec] | None
    is_active: bool


# --- the whole form ---------------------------------------------------------------


class RubricFormSection(RubricSectionResponse):
    items: list[RubricItemResponse]
    children: list["RubricFormSection"]


class RubricFormCategory(RubricCategoryResponse):
    sections: list[RubricFormSection]


class RubricFormResponse(RubricVersionResponse):
    categories: list[RubricFormCategory]
