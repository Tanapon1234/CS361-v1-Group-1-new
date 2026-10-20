"""Demo workload data for 3 academic years (2566-2568), so the lecturer work page and the
peer test cases (TC1-TC3) have something to find.

    cd backend
    uv run python -m scripts.import_v1_lecturers     # first: the lecturers come from V1
    uv run python -m scripts.seed_workload_demo      # DB from .env
    uv run python -m scripts.seed_workload_demo --base-url http://localhost:8000

Runs once: if rubric version 2567-r1 already exists it stops without changing anything.
Everything goes through the API, so scores and statuses are computed by the server.

What testers will find:
- Prapaporn: work in every category in all 3 years (2566 approved, 2567 submitted,
  2568 draft) and publications in 2566-2568
- Thapana: 2567 has teaching, supervision and service, but no academic work (TC2 empty case)
- Kasidit: 2566 and 2568, nothing in 2567 (TC3)
- Tanatorn (dept chair), Nuttanont (dept committee), Wanida: some 2567 work
- Every other V1 lecturer: no workload at all
"""

import argparse
from datetime import date
from typing import Any

import httpx2

from scripts.api import add_target_arguments, as_, call, find_lecturer, find_one, open_api

RUBRIC_CODE = "2567-r1"
YEARS = (2566, 2567, 2568)

PEOPLE = {
    "main": "rattanat@tu.ac.th",
    "teaching_only": "thapana@cs.tu.ac.th",
    "gap_year": "ckasidit@tu.ac.th",
    "coauthor": "wanidap@cs.tu.ac.th",
    "chair": "tanatorn@tu.ac.th",
    "committee": "nuttanon@tu.ac.th",
    "receiver": "skn@cs.tu.ac.th",
}

# Rubric version 1 from database/data_schema/SemesterReport/schema-reference.md, without the
# items that need an executive's assessment (3.1, 3.2) so demo submissions can be approved.
RUBRIC: list[dict[str, Any]] = [
    {
        "code": "1",
        "name_th": "งานสอน",
        "cap": 900,
        "sections": [
            {
                "code": "1.1",
                "name_th": "วิชาบรรยาย",
                "items": [
                    {
                        "key": "lecture_s",
                        "label_th": "นักศึกษา < 100 คน",
                        "weight": 1.0,
                        "unit": "credit",
                        "unit_divisor": 3,
                        "counts_teaching_credit": True,
                        "tier_min": 0,
                        "tier_max": 99,
                        "field_schema": {"hours": {"type": "int", "required": True}},
                    },
                    {
                        "key": "lecture_m",
                        "label_th": "นักศึกษา 100-250 คน",
                        "weight": 1.1,
                        "unit": "credit",
                        "unit_divisor": 3,
                        "counts_teaching_credit": True,
                        "tier_min": 100,
                        "tier_max": 250,
                        "field_schema": {"hours": {"type": "int", "required": True}},
                    },
                ],
            },
            {
                "code": "1.4",
                "name_th": "ซีเนียร์โปรเจกหรือปัญหาพิเศษ",
                "cap": 200,
                "items": [
                    {
                        "key": "project_advisor",
                        "label_th": "เป็นอาจารย์ที่ปรึกษา",
                        "weight": 0.2,
                        "unit": "topic",
                    },
                    {
                        "key": "project_examiner",
                        "label_th": "เป็นกรรมการสอบ",
                        "weight": 0.05,
                        "unit": "topic",
                    },
                ],
            },
            {
                "code": "1.9",
                "name_th": "วิทยานิพนธ์ ใน คณะ/มธ.",
                "items": [
                    {
                        "key": "thesis_advisor",
                        "label_th": "ที่ปรึกษาหลัก",
                        "weight": 0.1,
                        "unit": "credit",
                    },
                ],
            },
        ],
    },
    {
        "code": "2",
        "name_th": "งานวิชาการ",
        "cap": 900,
        "sections": [
            {
                "code": "2.3.1",
                "name_th": "วารสารระดับนานาชาติ",
                "items": [
                    {
                        "key": "journal_q1",
                        "label_th": "บทความวิจัย Q1",
                        "weight": 2.25,
                        "unit": "topic",
                        "uses_participation": True,
                        "field_schema": {
                            "quartile": {
                                "type": "enum",
                                "values": ["Tier1", "Q1", "Q2", "Q3", "Q4", "none"],
                            }
                        },
                    },
                    {
                        "key": "journal_q2",
                        "label_th": "บทความวิจัย Q2",
                        "weight": 2.0,
                        "unit": "topic",
                        "uses_participation": True,
                        "field_schema": {
                            "quartile": {
                                "type": "enum",
                                "values": ["Tier1", "Q1", "Q2", "Q3", "Q4", "none"],
                            }
                        },
                    },
                ],
            },
            {
                "code": "2.4.1",
                "name_th": "นำเสนอผลงานระดับนานาชาติ",
                "items": [
                    {
                        "key": "oral",
                        "label_th": "นำเสนอแบบบรรยาย",
                        "weight": 0.75,
                        "unit": "topic",
                        "uses_participation": True,
                    },
                    {
                        "key": "poster",
                        "label_th": "นำเสนอแบบโปสเตอร์",
                        "weight": 0.375,
                        "unit": "topic",
                        "uses_participation": True,
                    },
                ],
            },
        ],
    },
    {
        "code": "3",
        "name_th": "งานบริหาร",
        "cap": 400,
        "sections": [
            {
                "code": "3.3",
                "name_th": "ผู้ประสานงานประจำวิชา",
                "cap": 75,
                "items": [
                    {
                        "key": "coordinator",
                        "label_th": "ผู้ประสานงานวิชาที่มีผู้สอน 2-4 คน",
                        "weight": 0.10,
                        "unit": "course",
                    },
                ],
            },
            {
                "code": "3.5",
                "name_th": "งานอาจารย์ที่ปรึกษา",
                "items": [
                    {
                        "key": "advisor",
                        "label_th": "อาจารย์ที่ปรึกษาทั่วไป",
                        "weight": 0.125,
                        "unit": "person",
                    },
                ],
            },
        ],
    },
    {
        "code": "4",
        "name_th": "งานบริการวิชาการและอื่น ๆ",
        "cap": 300,
        "sections": [
            {
                "code": "4.1.1",
                "name_th": "คณะทำงานหรือกรรมการมีวาระ",
                "max_entries": 20,
                "items": [
                    {"key": "committee", "label_th": "คณะทำงาน", "weight": 0.05, "unit": "topic"},
                ],
            },
            {
                "code": "4.3",
                "name_th": "บริการวิชาการแก่สังคม",
                "items": [
                    {
                        "key": "speaker",
                        "label_th": "วิทยากรหรือผู้ทรงคุณวุฒิ",
                        "weight": 0.075,
                        "unit": "topic",
                    },
                ],
            },
            {
                "code": "4.4",
                "name_th": "ผู้ประเมินผลงานทางวิชาการ",
                "cap": 100,
                "items": [
                    {
                        "key": "reviewer",
                        "label_th": "ผู้ประเมินระดับนานาชาติ",
                        "weight": 0.075,
                        "unit": "topic",
                    },
                ],
            },
        ],
    },
    {"code": "5", "name_th": "คะแนนพิเศษ", "cap": 100, "sections": []},
]


def teach(item: str, course: str, title: str, students: int, credits: int = 3) -> dict:
    return {
        "item": item,
        "course_code": course,
        "title": title,
        "student_count": students,
        "quantity": credits,
        "credits": credits,
        "details": {"hours": credits * 15},
    }


def topic(item: str, title: str, quantity: float = 1, **extra: Any) -> dict:
    return {"item": item, "title": title, "quantity": quantity, **extra}


def paper(item: str, title: str, quartile: str, share: int) -> dict:
    return topic(item, title, participation_pct=share, details={"quartile": quartile})


# Entries per person and year. "status" is how far the submission goes.
WORK: dict[str, dict[int, dict[str, Any]]] = {
    "main": {
        2566: {
            "status": "dept_approved",
            "entries": [
                teach("lecture_s", "CS361", "Cloud Computing", 85),
                teach("lecture_m", "CS101", "Discrete Structures", 180),
                topic("project_advisor", "ระบบจองห้องสมุดบนคลาวด์", 2),
                paper("journal_q2", "Container migration with adaptive parallel TCP", "Q2", 50),
                topic("coordinator", "CS361 Cloud Computing"),
                topic("speaker", "อบรม AWS สำหรับครูมัธยม"),
            ],
        },
        2567: {
            "status": "submitted",
            "entries": [
                teach("lecture_s", "CS361", "Cloud Computing", 92),
                topic("project_advisor", "แพลตฟอร์มผลงานอาจารย์", 3),
                topic("thesis_advisor", "Serverless scheduling", 6),
                paper("journal_q1", "Serverless workflow scheduling at the edge", "Q1", 60),
                topic("oral", "IEEE CloudCom 2024"),
                topic("advisor", "นักศึกษาชั้นปีที่ 2", 25),
                topic("reviewer", "ผู้ประเมินบทความ IEEE Access", 2),
            ],
        },
        2568: {
            "status": "draft",
            "entries": [
                teach("lecture_s", "CS361", "Cloud Computing", 95),
                paper("journal_q2", "Cost-aware autoscaling for teaching labs", "Q2", 100),
                topic("committee", "คณะทำงานหลักสูตร"),
            ],
        },
    },
    "teaching_only": {
        2567: {
            "status": "submitted",
            "entries": [
                teach("lecture_m", "CS211", "Data Structures", 210),
                teach("lecture_s", "CS422", "Machine Learning", 70),
                topic("project_examiner", "กรรมการสอบโครงงาน", 6),
                topic("speaker", "บรรยายพิเศษ Data Science"),
            ],
        },
    },
    "gap_year": {
        2566: {
            "status": "dept_approved",
            "entries": [
                teach("lecture_s", "CS341", "Operating Systems", 60),
                topic("poster", "HPC Asia 2023"),
            ],
        },
        2568: {
            "status": "draft",
            "entries": [
                teach("lecture_s", "CS341", "Operating Systems", 64),
                topic("advisor", "นักศึกษาชั้นปีที่ 1", 20),
            ],
        },
    },
    "coauthor": {
        2567: {
            "status": "draft",
            "entries": [
                teach("lecture_s", "CS284", "Software Engineering", 80),
                paper("journal_q1", "Serverless workflow scheduling at the edge", "Q1", 40),
            ],
        },
    },
    "chair": {
        2567: {
            "status": "submitted",
            "entries": [
                teach("lecture_s", "CS372", "Health Informatics", 45),
                topic("committee", "กรรมการประจำคณะ"),
            ],
        },
    },
    "committee": {
        2567: {
            "status": "draft",
            "entries": [
                teach("lecture_m", "CS102", "Programming", 240),
            ],
        },
    },
}

# (title, C.E. year, venue, authors in order)
PUBLICATIONS = [
    ("Container migration with adaptive parallel TCP", 2023, "IEEE Access", ["main"]),
    (
        "Serverless workflow scheduling at the edge",
        2024,
        "Future Generation Computer Systems",
        ["main", "coauthor"],
    ),
    ("Cost-aware autoscaling for teaching labs", 2025, "IEEE Transactions on Education", ["main"]),
    ("Operating systems labs on shared clusters", 2023, "HPC Asia", ["gap_year"]),
]


def build_rubric(api: httpx2.Client) -> dict[str, int]:
    version = call(
        api,
        "POST",
        "/rubric-versions",
        json={
            "code": RUBRIC_CODE,
            "approved_meeting": "6/2567",
            "approved_on": "2024-05-27",
        },
    )
    items: dict[str, int] = {}
    for c_order, category in enumerate(RUBRIC, start=1):
        created = call(
            api,
            "POST",
            f"/rubric-versions/{version['id']}/categories",
            json={
                "code": category["code"],
                "name_th": category["name_th"],
                "cap": category["cap"],
                "sort_order": c_order * 10,
            },
        )
        for s_order, section in enumerate(category["sections"], start=1):
            body = {k: v for k, v in section.items() if k != "items"}
            new_section = call(
                api,
                "POST",
                f"/rubric-categories/{created['id']}/sections",
                json=body | {"sort_order": s_order * 10},
            )
            for item in section["items"]:
                key = item["key"]
                body = {k: v for k, v in item.items() if k != "key"}
                items[key] = call(
                    api, "POST", f"/rubric-sections/{new_section['id']}/items", json=body
                )["id"]
    return items


def build_rounds(api: httpx2.Client, version_id: int) -> dict[int, int]:
    rounds = {}
    for year in YEARS:
        ce = year - 543
        rounds[year] = call(
            api,
            "POST",
            "/rounds",
            json={
                "rubric_version_id": version_id,
                "name_th": f"รอบประเมินปีการศึกษา {year}",
                "period_start": date(ce, 8, 1).isoformat(),
                "period_end": date(ce + 1, 7, 31).isoformat(),
                "salary_effective_on": date(ce + 1, 10, 1).isoformat(),
                "academic_year": year,
                "is_open": True,
            },
        )["id"]
    return rounds


def approve(api: httpx2.Client, submission_id: str, actor: str) -> None:
    call(
        api,
        "POST",
        f"/submissions/{submission_id}/approvals",
        json={"decision": "approved"},
        headers=as_(actor),
    )


def seed(api: httpx2.Client) -> bool:
    """Create the demo data; False if it was already there."""
    if find_one(api, "/rubric-versions", "code", RUBRIC_CODE) is not None:
        print(f"Rubric {RUBRIC_CODE} already exists: demo data was seeded before, nothing to do")
        return False

    ids: dict[str, str] = {}
    for role, email in PEOPLE.items():
        lecturer = find_lecturer(api, email)
        if lecturer is None:
            raise SystemExit(f"{email} not found: run scripts.import_v1_lecturers first")
        ids[role] = lecturer["lecturer_id"]

    department = find_one(api, "/departments", "code", "CS") or call(
        api, "POST", "/departments", json={"code": "CS", "name_th": "วิทยาการคอมพิวเตอร์"}
    )
    lecturers = call(api, "GET", "/lecturers", params={"limit": 100})["items"]
    for lecturer in lecturers:
        if lecturer["department_id"] is None:
            call(
                api,
                "PATCH",
                f"/lecturers/{lecturer['lecturer_id']}",
                json={"department_id": department["id"]},
            )

    start = date(YEARS[0] - 543, 8, 1).isoformat()
    for role, position in (("chair", "dept_chair"), ("committee", "dept_committee")):
        call(
            api,
            "POST",
            f"/lecturers/{ids[role]}/positions",
            json={
                "position": position,
                "department_id": department["id"],
                "start_date": start,
            },
        )

    items = build_rubric(api)
    version_id = find_one(api, "/rubric-versions", "code", RUBRIC_CODE)["id"]
    rounds = build_rounds(api, version_id)

    for role, years in WORK.items():
        owner = ids[role]
        for year, plan in years.items():
            submission = call(
                api, "POST", "/submissions", json={"round_id": rounds[year]}, headers=as_(owner)
            )
            for order, entry in enumerate(plan["entries"]):
                body = {k: v for k, v in entry.items() if k != "item"}
                call(
                    api,
                    "POST",
                    f"/submissions/{submission['id']}/entries",
                    json=body | {"item_id": items[entry["item"]], "sort_order": order},
                    headers=as_(owner),
                )
            status = plan["status"]
            if status in ("submitted", "dept_approved"):
                approve(api, submission["id"], owner)
            if status == "dept_approved":
                approve(api, submission["id"], ids["receiver"])  # -> assessing
                approve(api, submission["id"], ids["chair"])  # -> dept_review
                approve(api, submission["id"], ids["committee"])  # -> dept_approved
            print(f"{role:<14} {year}  {len(plan['entries'])} entries  {status}")

    for year in YEARS[:-1]:
        call(api, "PATCH", f"/rounds/{rounds[year]}", json={"is_open": False})

    for title, year, venue, authors in PUBLICATIONS:
        call(
            api,
            "POST",
            "/publications",
            json={
                "title": title,
                "publication_year": year,
                "venue": venue,
                "lecturer_ids": [ids[author] for author in authors],
            },
        )
    print(f"Done: rubric {RUBRIC_CODE}, {len(YEARS)} rounds, {len(PUBLICATIONS)} publications")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_target_arguments(parser)
    args = parser.parse_args()
    with open_api(args.base_url) as api:
        seed(api)


if __name__ == "__main__":
    main()
