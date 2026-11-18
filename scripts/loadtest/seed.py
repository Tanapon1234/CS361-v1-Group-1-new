"""Seed or remove load-test data (V6, #319).

Every row is reachable from a lecturer whose email ends with @loadtest.invalid, so
`cleanup` removes exactly what `seed` made and never touches real data.

  cd backend
  uv run python ../scripts/loadtest/seed.py seed    --database-url postgresql://postgres:local@127.0.0.1:5434/cs361_perf
  uv run python ../scripts/loadtest/seed.py cleanup --database-url ...

Only point this at a development or test database.
"""

from __future__ import annotations

import argparse

import psycopg

DOMAIN = "@loadtest.invalid"

SEED_SQL = """
WITH dept AS (SELECT id FROM department WHERE id = %(department)s),
new_lecturers AS (
  INSERT INTO lecturer (name_th, email, rank, is_active, department_id)
  SELECT 'ทดสอบ ' || lpad(n::text, 4, '0'), 'loadtest-' || lpad(n::text, 4, '0') || %(domain)s,
         'lecturer', true, %(department)s
  FROM generate_series(1, %(lecturers)s) AS n
  RETURNING lecturer_id, email
),
numbered AS (
  SELECT lecturer_id, row_number() OVER (ORDER BY email) AS n FROM new_lecturers
),
-- every 10th lecturer submits nothing, so the report's "missing" list has content
new_submissions AS (
  INSERT INTO submission (round_id, lecturer_id, status, rank_snapshot, department_snapshot,
                          raw_total, capped_total)
  SELECT r.id, n.lecturer_id,
         CASE WHEN n.n <= %(accounts)s AND r.academic_year = %(year_to)s THEN 'draft' ELSE 'submitted' END::submission_status,
         'lecturer', %(department)s, 100, 90
  FROM numbered n
  JOIN evaluation_round r ON r.academic_year BETWEEN %(year_from)s AND %(year_to)s
  WHERE n.n %% 10 <> 0
  RETURNING id
)
INSERT INTO submission_category_total (submission_id, category_id, raw_score, capped_score)
SELECT s.id, c.id, 20, 18 FROM new_submissions s CROSS JOIN rubric_category c
"""

CLEANUP_SQL = [
    "DELETE FROM submission_category_total WHERE submission_id IN (SELECT s.id FROM submission s "
    "JOIN lecturer l USING (lecturer_id) WHERE l.email LIKE %(like)s)",
    "DELETE FROM submission_entry WHERE submission_id IN (SELECT s.id FROM submission s "
    "JOIN lecturer l USING (lecturer_id) WHERE l.email LIKE %(like)s)",
    "DELETE FROM submission WHERE lecturer_id IN (SELECT lecturer_id FROM lecturer WHERE email LIKE %(like)s)",
    "DELETE FROM lecturer WHERE email LIKE %(like)s",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("action", choices=["seed", "cleanup"])
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--lecturers", type=int, default=400)
    parser.add_argument("--department", type=int, default=1)
    parser.add_argument("--year-from", type=int, default=2568)
    parser.add_argument("--year-to", type=int, default=2572)
    parser.add_argument("--accounts", type=int, default=10, help="first N lecturers get a draft sheet in the last year, for write tests")
    args = parser.parse_args()

    with psycopg.connect(args.database_url) as conn:
        if args.action == "seed":
            exists = conn.execute(
                "SELECT count(*) FROM lecturer WHERE email LIKE %s", (f"loadtest-%{DOMAIN}",)
            ).fetchone()[0]
            if exists:
                raise SystemExit(f"{exists} load-test lecturers already exist; run cleanup first")
            conn.execute(
                SEED_SQL,
                {
                    "domain": DOMAIN,
                    "department": args.department,
                    "lecturers": args.lecturers,
                    "year_from": args.year_from,
                    "year_to": args.year_to,
                    "accounts": args.accounts,
                },
            )
        else:
            for statement in CLEANUP_SQL:
                conn.execute(statement, {"like": f"loadtest-%{DOMAIN}"})
        total = conn.execute(
            "SELECT (SELECT count(*) FROM lecturer WHERE email LIKE %s), "
            "(SELECT count(*) FROM submission), (SELECT count(*) FROM submission_category_total)",
            (f"loadtest-%{DOMAIN}",),
        ).fetchone()
    print(f"{args.action} done: load-test lecturers={total[0]}, submissions(all)={total[1]}, category totals(all)={total[2]}")


if __name__ == "__main__":
    main()
