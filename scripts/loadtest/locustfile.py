"""Locust scenario for the three most common actions (V6, #319).

  list    GET  /api/v3/submissions?lecturer_id=<me>          (a lecturer's own sheets)
  detail  GET  /api/v3/submissions/{id}                       (open one sheet)
  report  GET  /api/v3/departments/{id}/report                (department summary, the heaviest read)
  write   POST /api/v3/submissions/{id}/entries               (add a workload entry, ~20% of calls)

Accounts are the lecturers made by seed.py (their draft sheet is the write target).
Local dev auth:   locust -f locustfile.py --host http://127.0.0.1:8010
Real deployment:  LOADTEST_TOKENS=tok1,tok2,... locust -f locustfile.py --host https://<api>
                  (Cognito ID tokens of test accounts; one needs a role that may read the report)

Headless example (1000 users is too many for one laptop; start with 50):
  locust -f locustfile.py --host ... --headless -u 50 -r 10 -t 2m --csv result
"""

from __future__ import annotations

import itertools
import os
import random

from locust import HttpUser, between, events, task

DEPARTMENT_ID = int(os.environ.get("LOADTEST_DEPARTMENT_ID", "1"))
YEAR_FROM = int(os.environ.get("LOADTEST_YEAR_FROM", "2568"))
YEAR_TO = int(os.environ.get("LOADTEST_YEAR_TO", "2572"))
TOKENS = [t for t in os.environ.get("LOADTEST_TOKENS", "").split(",") if t]
ADMIN = {"X-Dev-Roles": "admin"}

_accounts: list[str] = []
_next = itertools.count()


@events.test_start.add_listener
def discover_accounts(environment, **_kwargs) -> None:
    """Find the seeded test lecturers once (dev-header mode only)."""
    if TOKENS:
        return
    import requests

    response = requests.get(
        f"{environment.host}/api/v3/lecturers",
        params={"q": "loadtest-", "limit": 10},
        headers={"X-Lecturer-Id": "00000000-0000-0000-0000-000000000000", **ADMIN},
        timeout=30,
    )
    response.raise_for_status()
    _accounts.extend(item["lecturer_id"] for item in response.json()["items"])
    if not _accounts:
        raise SystemExit("no loadtest-* lecturers found; run seed.py first")


class Lecturer(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        index = next(_next)
        if TOKENS:
            self.headers = {"Authorization": f"Bearer {TOKENS[index % len(TOKENS)]}"}
            me = self.client.get("/api/v3/me", headers=self.headers, name="/me").json()
            self.lecturer_id = me["lecturer"]["lecturer_id"]
        else:
            self.lecturer_id = _accounts[index % len(_accounts)]
            self.headers = {"X-Lecturer-Id": self.lecturer_id, **ADMIN}
        sheets = self.client.get(
            "/api/v3/submissions",
            params={"lecturer_id": self.lecturer_id},
            headers=self.headers,
            name="/submissions?lecturer_id",
        ).json()["items"]
        self.sheet_ids = [s["id"] for s in sheets]
        drafts = [s["id"] for s in sheets if s["status"] == "draft"]
        self.draft_id = drafts[0] if drafts else None

    @task(6)
    def list_my_sheets(self) -> None:
        self.client.get(
            "/api/v3/submissions",
            params={"lecturer_id": self.lecturer_id},
            headers=self.headers,
            name="/submissions?lecturer_id",
        )

    @task(5)
    def open_sheet(self) -> None:
        if self.sheet_ids:
            self.client.get(
                f"/api/v3/submissions/{random.choice(self.sheet_ids)}",
                headers=self.headers,
                name="/submissions/{id}",
            )

    @task(5)
    def department_report(self) -> None:
        self.client.get(
            f"/api/v3/departments/{DEPARTMENT_ID}/report",
            params={"academic_year_from": YEAR_FROM, "academic_year_to": YEAR_TO},
            headers=self.headers,
            name="/departments/{id}/report",
        )

    @task(4)
    def add_entry(self) -> None:
        if self.draft_id:
            self.client.post(
                f"/api/v3/submissions/{self.draft_id}/entries",
                json={"item_id": 3, "title": "loadtest", "quantity": 1},
                headers=self.headers,
                name="POST /submissions/{id}/entries",
            )
