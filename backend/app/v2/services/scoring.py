"""Workload scoring rules: pure functions, no database, so they are easy to test.

Formula (database/data_schema/SemesterReport/schema-reference.md):

    score = (quantity / unit_divisor) x weight x base_points x participation_pct / 100

- fixed item:  weight = rubric_item.weight
- ranged item: the assessors' values are combined (single / average)
    - range_basis = weight -> the value is the weight in the formula above
    - range_basis = points -> the value is the score itself
  Until someone assesses it, weight_applied is NULL and score is 0.

Caps: a section is capped at `rubric_section.cap` (its own entries + its sub-sections),
a category at `rubric_category.cap`, the whole form at `rubric_version.overall_cap`.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.v2.models.enums import AssessmentAgg, RangeBasis, WeightMode
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection

HUNDRED = Decimal(100)
ZERO = Decimal(0)


def round_score(value: Decimal) -> Decimal:
    """numeric(8,2)"""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_weight(value: Decimal) -> Decimal:
    """numeric(8,4)"""
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# --- one entry --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EntryScore:
    weight_applied: Decimal | None
    score: Decimal


def combine_assessments(agg: AssessmentAgg, values: Sequence[Decimal]) -> Decimal:
    if agg is AssessmentAgg.SINGLE:
        return values[0]
    return sum(values, ZERO) / len(values)


def score_entry(
    *,
    item: RubricItem,
    quantity: Decimal,
    participation_pct: Decimal,
    base_points: Decimal,
    assessed_values: Sequence[Decimal] = (),
) -> EntryScore:
    multiplier = quantity / item.unit_divisor * participation_pct / HUNDRED

    if item.weight_mode is WeightMode.FIXED:
        weight = item.weight if item.weight is not None else ZERO
        return EntryScore(round_weight(weight), round_score(multiplier * weight * base_points))

    if not assessed_values:
        return EntryScore(None, ZERO)
    value = combine_assessments(item.assessment_agg, assessed_values)
    if item.range_basis is RangeBasis.POINTS:
        return EntryScore(None, round_score(value))
    return EntryScore(round_weight(value), round_score(multiplier * value * base_points))


def needs_assessment(item: RubricItem) -> bool:
    return item.weight_mode is WeightMode.RANGED


# --- validating an entry against its item ------------------------------------------

# field_schema keys that are real submission_entry columns are checked on the column.
ENTRY_COLUMNS = ("title", "course_code", "section_no", "student_count", "credits")


def _check_type(name: str, spec: Mapping[str, Any], value: Any) -> str | None:
    kind = spec.get("type")
    is_number = isinstance(value, int | float | Decimal) and not isinstance(value, bool)
    if kind == "int" and not (isinstance(value, int) and not isinstance(value, bool)):
        return f"{name} must be an integer"
    if kind == "number" and not is_number:
        return f"{name} must be a number"
    if kind == "money" and not (is_number and value >= 0):
        return f"{name} must be an amount >= 0"
    if kind == "string" and not isinstance(value, str):
        return f"{name} must be text"
    if kind == "bool" and not isinstance(value, bool):
        return f"{name} must be true or false"
    if kind == "enum" and value not in spec.get("values", []):
        return f"{name} must be one of {spec.get('values', [])}"
    if kind == "date":
        try:
            date.fromisoformat(str(value))
        except ValueError:
            return f"{name} must be a date (YYYY-MM-DD)"
    return None


def validate_details(
    field_schema: Mapping[str, Any] | None,
    details: Mapping[str, Any] | None,
    columns: Mapping[str, Any],
) -> list[str]:
    """Check `details` (and the entry columns named in the schema) against `field_schema`."""
    if not field_schema:
        return []
    details = details or {}
    errors = [
        f"details.{key} is not a field of this item"
        for key in details
        if key not in field_schema or key in ENTRY_COLUMNS
    ]
    for name, spec in field_schema.items():
        value = columns.get(name) if name in ENTRY_COLUMNS else details.get(name)
        if value is None:
            if spec.get("required"):
                errors.append(f"{name} is required for this item")
            continue
        error = _check_type(name, spec, value)
        if error:
            errors.append(error)
    return errors


def validate_entry(
    item: RubricItem,
    *,
    student_count: int | None,
    participation_pct: Decimal,
    details: Mapping[str, Any] | None,
    columns: Mapping[str, Any],
) -> list[str]:
    """Rules that come from the rubric item. Returns error messages (empty = valid)."""
    errors: list[str] = []
    if item.tier_min is not None or item.tier_max is not None:
        if student_count is None:
            errors.append("student_count is required for this item")
        elif (item.tier_min is not None and student_count < item.tier_min) or (
            item.tier_max is not None and student_count > item.tier_max
        ):
            errors.append(
                f"student_count {student_count} is outside this item's range "
                f"({item.tier_min}-{item.tier_max if item.tier_max is not None else '...'})"
            )
    if not item.uses_participation and participation_pct != HUNDRED:
        errors.append("participation_pct must be 100 for this item")
    errors.extend(validate_details(item.field_schema, details, columns))
    return errors


def validate_assessment_value(item: RubricItem, value: Decimal) -> str | None:
    low, high = item.weight_min, item.weight_max
    if low is not None and value < low:
        return f"value_given must be between {low} and {high}"
    if high is not None and value > high:
        return f"value_given must be between {low} and {high}"
    return None


# --- totals of a whole submission --------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScoredEntry:
    item: RubricItem
    score: Decimal
    credits: Decimal | None


@dataclass(slots=True)
class Totals:
    raw_total: Decimal
    capped_total: Decimal
    teaching_credits: Decimal
    # category_id -> (raw, capped)
    categories: dict[int, tuple[Decimal, Decimal]] = field(default_factory=dict)
    # section_id -> (raw, capped)
    sections: dict[int, tuple[Decimal, Decimal]] = field(default_factory=dict)


def _cap(value: Decimal, cap: Decimal | None) -> Decimal:
    return value if cap is None else min(value, cap)


def compute_totals(
    *,
    categories: Iterable[RubricCategory],
    sections: Iterable[RubricSection],
    entries: Iterable[ScoredEntry],
    overall_cap: Decimal,
) -> Totals:
    sections_by_id = {section.id: section for section in sections if section.id is not None}
    children: dict[int, list[int]] = defaultdict(list)
    for section in sections_by_id.values():
        if section.parent_id is not None and section.parent_id in sections_by_id:
            children[section.parent_id].append(section.id)

    direct: dict[int, Decimal] = defaultdict(lambda: ZERO)
    teaching_credits = ZERO
    for entry in entries:
        direct[entry.item.section_id] += entry.score
        if entry.item.counts_teaching_credit and entry.credits is not None:
            teaching_credits += entry.credits

    section_totals: dict[int, tuple[Decimal, Decimal]] = {}

    def total_of(section_id: int) -> tuple[Decimal, Decimal]:
        if section_id not in section_totals:
            raw, capped = direct[section_id], direct[section_id]
            for child_id in children[section_id]:
                child_raw, child_capped = total_of(child_id)
                raw += child_raw
                capped += child_capped
            section_totals[section_id] = (raw, _cap(capped, sections_by_id[section_id].cap))
        return section_totals[section_id]

    category_totals: dict[int, tuple[Decimal, Decimal]] = {}
    for category in categories:
        roots = [
            section.id
            for section in sections_by_id.values()
            if section.category_id == category.id
            and (section.parent_id is None or section.parent_id not in sections_by_id)
        ]
        raw = sum((total_of(sid)[0] for sid in roots), ZERO)
        capped = sum((total_of(sid)[1] for sid in roots), ZERO)
        category_totals[category.id] = (raw, _cap(capped, category.cap))

    raw_total = sum((raw for raw, _ in category_totals.values()), ZERO)
    capped_total = min(sum((capped for _, capped in category_totals.values()), ZERO), overall_cap)
    return Totals(
        raw_total=raw_total,
        capped_total=capped_total,
        teaching_credits=teaching_credits,
        categories=category_totals,
        sections=section_totals,
    )
