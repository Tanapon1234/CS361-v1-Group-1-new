"""The scoring formula and caps, with the worked examples of schema-reference.md."""

from decimal import Decimal

import pytest

from app.v2.models.enums import AssessmentAgg, QuantityUnit, RangeBasis, WeightMode
from app.v2.models.rubric import RubricCategory, RubricItem, RubricSection
from app.v2.services.scoring import (
    ScoredEntry,
    compute_totals,
    score_entry,
    validate_assessment_value,
    validate_entry,
)

D = Decimal


def fixed(weight: str, divisor: str = "1", **extra: object) -> RubricItem:
    values: dict[str, object] = {"id": 1, "section_id": 1, "label_th": "x"} | extra
    return RubricItem(weight=D(weight), unit=QuantityUnit.TOPIC, unit_divisor=D(divisor), **values)


def ranged(basis: RangeBasis, agg: AssessmentAgg, low: str, high: str) -> RubricItem:
    return RubricItem(
        id=2,
        section_id=1,
        label_th="x",
        weight_mode=WeightMode.RANGED,
        weight_min=D(low),
        weight_max=D(high),
        range_basis=basis,
        assessment_agg=agg,
        unit=QuantityUnit.TERM,
    )


@pytest.mark.parametrize(
    ("item", "quantity", "pct", "expected"),
    [
        (fixed("1.0", "3"), "3", "100", "200.00"),  # 1.1 CS222 3 credits
        (fixed("0.2"), "3", "100", "120.00"),  # 1.5 co-op, 3 topics
        (fixed("0.1"), "6", "100", "120.00"),  # 1.9 thesis, 6 credits
        (fixed("1.25"), "1", "20", "50.00"),  # 2.3.1 article, 20% share
        (fixed("0.05"), "1", "100", "10.00"),  # 4.2.1 committee
    ],
)
def test_fixed_items_follow_the_formula(
    item: RubricItem, quantity: str, pct: str, expected: str
) -> None:
    result = score_entry(
        item=item, quantity=D(quantity), participation_pct=D(pct), base_points=D(200)
    )
    assert result.score == D(expected)
    assert result.weight_applied == item.weight


def test_ranged_weight_item_averages_the_assessors() -> None:
    item = ranged(RangeBasis.WEIGHT, AssessmentAgg.AVERAGE, "1.0", "2.0")

    result = score_entry(
        item=item,
        quantity=D(1),
        participation_pct=D(100),
        base_points=D(200),
        assessed_values=[D("1.8"), D("1.5"), D("1.6")],
    )

    assert (result.weight_applied, result.score) == (D("1.6333"), D("326.67"))


def test_ranged_points_item_uses_the_value_as_score() -> None:
    item = ranged(RangeBasis.POINTS, AssessmentAgg.SINGLE, "50", "100")

    result = score_entry(
        item=item,
        quantity=D(1),
        participation_pct=D(100),
        base_points=D(200),
        assessed_values=[D(85)],
    )

    assert (result.weight_applied, result.score) == (None, D("85.00"))


def test_ranged_item_without_assessment_scores_zero() -> None:
    item = ranged(RangeBasis.WEIGHT, AssessmentAgg.AVERAGE, "1.0", "2.0")
    result = score_entry(item=item, quantity=D(1), participation_pct=D(100), base_points=D(200))
    assert (result.weight_applied, result.score) == (None, D(0))


def test_totals_apply_section_category_and_overall_caps() -> None:
    teaching = RubricCategory(id=1, version_id=1, code="1", name_th="สอน", cap=D(900), sort_order=1)
    service = RubricCategory(
        id=4, version_id=1, code="4", name_th="บริการ", cap=D(300), sort_order=4
    )
    group = RubricSection(id=10, category_id=1, code="A", name_th="ป.ตรี", sort_order=1)
    seminar = RubricSection(
        id=11, category_id=1, parent_id=10, code="1.3", name_th="สัมมนา", cap=D(120), sort_order=2
    )
    lecture = RubricSection(
        id=12, category_id=1, parent_id=10, code="1.1", name_th="บรรยาย", sort_order=3
    )
    committee = RubricSection(id=40, category_id=4, code="4.1", name_th="กรรมการ", sort_order=1)

    def entry(section_id: int, score: int, credits: int | None = None) -> ScoredEntry:
        item = fixed("1", section_id=section_id, counts_teaching_credit=credits is not None)
        return ScoredEntry(
            item=item, score=D(score), credits=None if credits is None else D(credits)
        )

    totals = compute_totals(
        categories=[teaching, service],
        sections=[group, seminar, lecture, committee],
        entries=[
            entry(11, 200),  # seminar capped at 120
            entry(12, 600, credits=9),
            entry(12, 400, credits=3),
            entry(40, 330),  # category 4 capped at 300
        ],
        overall_cap=D(1000),
    )

    assert totals.sections[11] == (D(200), D(120))
    assert totals.categories[1] == (D(1200), D(900))
    assert totals.categories[4] == (D(330), D(300))
    assert (totals.raw_total, totals.capped_total) == (D(1530), D(1000))
    assert totals.teaching_credits == D(12)


def test_validate_entry_checks_tier_participation_and_field_schema() -> None:
    item = fixed(
        "1",
        tier_min=0,
        tier_max=99,
        field_schema={
            "hours": {"type": "int", "required": True},
            "quartile": {"type": "enum", "values": ["Q1", "Q2"]},
        },
    )

    errors = validate_entry(
        item,
        student_count=150,
        participation_pct=D(50),
        details={"quartile": "Q9", "typo": 1},
        columns={},
    )

    assert errors == [
        "student_count 150 is outside this item's range (0-99)",
        "participation_pct must be 100 for this item",
        "details.typo is not a field of this item",
        "hours is required for this item",
        "quartile must be one of ['Q1', 'Q2']",
    ]
    assert (
        validate_entry(
            item, student_count=60, participation_pct=D(100), details={"hours": 45}, columns={}
        )
        == []
    )


def test_assessment_value_must_be_in_the_item_range() -> None:
    item = ranged(RangeBasis.WEIGHT, AssessmentAgg.AVERAGE, "1.0", "2.0")
    assert validate_assessment_value(item, D("1.5")) is None
    assert validate_assessment_value(item, D("2.5")) == "value_given must be between 1.0 and 2.0"
