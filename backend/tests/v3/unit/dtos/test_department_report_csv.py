import csv
import io
from decimal import Decimal
from uuid import uuid4

from app.v3.dtos.department_dto import (
    DepartmentReportCategoryRow,
    DepartmentReportMissingRow,
    DepartmentReportResponse,
    DepartmentResponse,
    department_report_to_csv,
)


def report(**values: object) -> DepartmentReportResponse:
    defaults = {
        "department": DepartmentResponse(id=1, code="CS", name_th="CS", is_active=True),
        "academic_year_from": 2566,
        "academic_year_to": 2568,
        "rows": [],
        "missing": [],
    }
    return DepartmentReportResponse(**(defaults | values))


def test_rows_and_missing_become_one_table() -> None:
    lecturer_id = uuid4()
    missing_id = uuid4()
    csv_text = department_report_to_csv(
        report(
            rows=[
                DepartmentReportCategoryRow(
                    lecturer_id=lecturer_id,
                    name_th="ปราภาพร",
                    academic_year=2567,
                    category_code="1",
                    category_name_th="งานสอน",
                    raw_score=Decimal("90"),
                    capped_score=Decimal("80"),
                )
            ],
            missing=[
                DepartmentReportMissingRow(
                    lecturer_id=missing_id, name_th="ฐาปนา", academic_year=2567
                )
            ],
        )
    )

    parsed = list(csv.reader(io.StringIO(csv_text)))
    assert parsed[0] == [
        "lecturer_name_th",
        "academic_year",
        "category_code",
        "category_name_th",
        "raw_score",
        "capped_score",
        "status",
    ]
    assert parsed[1] == ["ปราภาพร", "2567", "1", "งานสอน", "90", "80", "submitted"]
    assert parsed[2] == ["ฐาปนา", "2567", "", "", "", "", "missing"]
    assert len(parsed) == 3


def test_empty_report_is_header_only() -> None:
    parsed = list(csv.reader(io.StringIO(department_report_to_csv(report()))))
    assert len(parsed) == 1
