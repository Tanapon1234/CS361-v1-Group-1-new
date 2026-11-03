"""Peer test cases TC1-TC3 against the demo data (scripts/import_v1_lecturers.py +
scripts/seed_workload_demo.py) in a real PostgreSQL. How to run it: see support.py.
"""

from typing import Any

from fastapi.testclient import TestClient

from scripts.api import find_lecturer
from scripts.import_v1_lecturers import import_all
from scripts.seed_workload_demo import seed
from tests.v3.integration.support import ok, requires_database

pytestmark = requires_database


def work(api: TestClient, email: str, **params: Any) -> Any:
    lecturer_id = find_lecturer(api, email)["lecturer_id"]
    result = ok(api.get(f"/api/v3/lecturers/{lecturer_id}/work", params=params))
    assert result["lecturer_id"] == lecturer_id
    return result


def work_in_year(api: TestClient, email: str, academic_year: int, **params: Any) -> Any:
    return work(
        api, email, academic_year_from=academic_year, academic_year_to=academic_year, **params
    )


def entries(result: Any) -> list[Any]:
    return [
        entry
        for year in result["years"]
        for group in year["categories"]
        for entry in group["entries"]
    ]


def test_demo_data_answers_the_peer_test_cases(api: TestClient) -> None:
    assert import_all(api) == 22
    assert import_all(api) == 0  # matched by email the second time
    assert seed(api) is True
    assert seed(api) is False

    # TC1: one lecturer, one year, several categories, all from that year
    tc1 = work_in_year(api, "rattanat@tu.ac.th", 2567)
    assert len(tc1["years"]) == 1
    tc1_year = tc1["years"][0]
    assert tc1_year["academic_year"] == 2567
    assert {group["code"] for group in tc1_year["categories"]} == {"1", "2", "3", "4"}
    assert {entry["academic_year"] for entry in entries(tc1)} == {2567}
    assert [p["academic_year"] for p in tc1_year["publications"]] == [2567]
    assert tc1["available_years"][:3] == [2568, 2567, 2566]

    # TC2: research (category 2) of that year only
    tc2 = work_in_year(api, "rattanat@tu.ac.th", 2567, category="2")
    tc2_year = tc2["years"][0]
    assert [group["code"] for group in tc2_year["categories"]] == ["2"]
    assert {entry["academic_year"] for entry in entries(tc2)} == {2567}
    assert tc2["filters"]["category_name_th"] == "งานวิชาการ"
    assert tc2["total"] == len(entries(tc2)) + len(tc2_year["publications"]) == 3

    # A co-author's entry on the same paper stays with the co-author
    coauthor = work_in_year(api, "wanidap@cs.tu.ac.th", 2567, category="2")
    assert {e["submission_id"] for e in entries(coauthor)}.isdisjoint(
        {e["submission_id"] for e in entries(tc2)}
    )

    # TC3: nothing in that year / category: empty, but the filters and other years are there
    gap = work_in_year(api, "ckasidit@tu.ac.th", 2567)
    assert (gap["total"], gap["years"]) == (0, [])
    assert gap["filters"]["academic_year_from"] == 2567
    assert gap["filters"]["academic_year_to"] == 2567
    assert gap["available_years"] == [2568, 2566]

    no_research = work_in_year(api, "thapana@cs.tu.ac.th", 2567, category="2")
    assert no_research["total"] == 0
    assert work_in_year(api, "thapana@cs.tu.ac.th", 2567)["total"] == 4

    # A multi-year range groups results per year
    multi_year = work(api, "rattanat@tu.ac.th", academic_year_from=2566, academic_year_to=2568)
    assert [y["academic_year"] for y in multi_year["years"]] == sorted(
        {y["academic_year"] for y in multi_year["years"]}, reverse=True
    )
    assert 2567 in {y["academic_year"] for y in multi_year["years"]}

    nothing = work(api, "wpakorn@tu.ac.th")
    assert (nothing["total"], nothing["available_years"]) == (0, [])
