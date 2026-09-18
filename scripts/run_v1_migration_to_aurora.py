#!/usr/bin/env python3
"""Load the V1 -> V2 migration payload (build/v2/migration/*.json) into Aurora
via the RDS Data API, using the AWS CLI (no boto3 dependency required).

Idempotent: every insert is an ON CONFLICT ... DO UPDATE upsert keyed by the
deterministic ids produced by build_v1_migration_payload.py, so this can be
re-run safely after a rerun of the build step.

Requires (fetched from CloudFormation outputs if not set):
  AWS_REGION        (default: ap-southeast-1)
  DB_CLUSTER_ARN
  DB_SECRET_ARN
  DB_NAME           (default: cs361v2)
  FOUNDATION_STACK  (default: cs361-v2-aws-foundation-dev, used to look up
                     DB_CLUSTER_ARN/DB_SECRET_ARN/DB_NAME if not already set)

Usage:
  python3 scripts/build_v1_migration_payload.py         # build payload first
  python3 scripts/run_v1_migration_to_aurora.py --dry-run
  python3 scripts/run_v1_migration_to_aurora.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / "build" / "v2" / "migration"

CHUNK_SIZE = 40

# column -> value-type: text | int | numeric | date | timestamp | json
TABLE_SPECS = {
    "import_batch": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "source_system": "text",
            "source_name": "text",
            "source_version": "text",
            "source_type": "text",
            "source_s3_key": "text",
            "source_hash": "text",
            "status": "text",
            "record_count": "int",
            "valid_count": "int",
            "warning_count": "int",
            "error_count": "int",
            "started_at": "timestamp",
            "completed_at": "timestamp",
            "created_by": "text",
        },
    },
    "faculty": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "public_slug": "text",
            "name_th": "text",
            "name_en": "text",
            "academic_position": "text",
            "department": "text",
            "office_public": "text",
            "phone_public": "text",
            "email_public": "text",
            "profile_image_url": "text",
            "profile_image_alt": "text",
            "visibility": "text",
            "status": "text",
        },
    },
    "faculty_education": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "faculty_id": "text",
            "degree": "text",
            "field_of_study": "text",
            "institution": "text",
            "country": "text",
            "graduation_year": "int",
            "display_order": "int",
        },
    },
    "faculty_interest": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "faculty_id": "text",
            "interest_type": "text",
            "value": "text",
            "visibility": "text",
        },
    },
    "work_item": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "category_code": "text",
            "work_type_code": "text",
            "title": "text",
            "description": "text",
            "start_date": "date",
            "end_date": "date",
            "visibility": "text",
            "status": "text",
            "source_score": "numeric",
            "source_weight": "numeric",
            "source_section_code": "text",
            "import_batch_id": "text",
            "source_record_id": "text",
            "created_by": "text",
            "updated_by": "text",
        },
    },
    "publication_detail": {
        "conflict_key": "work_item_id",
        "columns": {
            "work_item_id": "text",
            "publication_title": "text",
            "venue": "text",
            "publisher": "text",
            "publication_year": "int",
            "publication_date": "date",
            "doi": "text",
            "isbn": "text",
            "issn": "text",
            "quartile": "text",
            "indexing_database": "text",
            "publication_kind": "text",
            "external_url": "text",
        },
    },
    "faculty_work_item": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "faculty_id": "text",
            "work_item_id": "text",
            "academic_period_id": "text",
            "evaluation_period_id": "text",
            "role": "text",
            "contribution_order": "int",
            "contribution_percent": "numeric",
            "contribution_note": "text",
            "quantity": "numeric",
            "credits": "numeric",
            "hours": "numeric",
            "source_section_code": "text",
        },
    },
    "source_record": {
        "conflict_key": "id",
        "columns": {
            "id": "text",
            "import_batch_id": "text",
            "source_system": "text",
            "source_record_key": "text",
            "source_section_code": "text",
            "source_hash": "text",
            "row_number": "int",
            "raw_record": "json",
            "target_entity_type": "text",
            "target_entity_id": "text",
            "status": "text",
            "error_message": "text",
        },
    },
}

# Insert order matters for FK integrity.
# source_record must precede work_item: work_item.source_record_id references it.
INSERT_ORDER = [
    "import_batch",
    "faculty",
    "faculty_education",
    "faculty_interest",
    "source_record",
    "work_item",
    "publication_detail",
    "faculty_work_item",
]


def to_timestamp_str(iso_value: str) -> str:
    dt = datetime.fromisoformat(iso_value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def build_param(value, value_type: str) -> dict:
    """Return an RDS Data API SqlParameter dict: {"value": {...}, "typeHint": "..."}."""
    if value is None:
        return {"value": {"isNull": True}}
    if value_type == "text":
        return {"value": {"stringValue": str(value)}}
    if value_type == "int":
        return {"value": {"longValue": int(value)}}
    if value_type == "numeric":
        return {"value": {"stringValue": str(value)}, "typeHint": "DECIMAL"}
    if value_type == "date":
        return {"value": {"stringValue": str(value)}, "typeHint": "DATE"}
    if value_type == "timestamp":
        return {"value": {"stringValue": to_timestamp_str(value)}, "typeHint": "TIMESTAMP"}
    if value_type == "json":
        return {"value": {"stringValue": json.dumps(value, ensure_ascii=False)}, "typeHint": "JSON"}
    raise ValueError(f"unknown value_type {value_type}")


def build_sql(table: str, spec: dict) -> str:
    columns = list(spec["columns"].keys())
    conflict_key = spec["conflict_key"]
    col_list = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    update_cols = [c for c in columns if c != conflict_key]
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    return (
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_key}) DO UPDATE SET {set_clause}"
    )


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def resolve_env(args) -> dict:
    region = args.region or os.environ.get("AWS_REGION", "ap-southeast-1")
    cluster_arn = os.environ.get("DB_CLUSTER_ARN")
    secret_arn = os.environ.get("DB_SECRET_ARN")
    db_name = os.environ.get("DB_NAME")

    if cluster_arn and secret_arn and db_name:
        return {"region": region, "cluster_arn": cluster_arn, "secret_arn": secret_arn, "db_name": db_name}

    stack = os.environ.get("FOUNDATION_STACK", "cs361-v2-aws-foundation-dev")
    print(f"DB_CLUSTER_ARN/DB_SECRET_ARN/DB_NAME not fully set, looking up from stack {stack} ...")
    proc = subprocess.run(
        [
            "aws", "cloudformation", "describe-stacks",
            "--region", region,
            "--stack-name", stack,
            "--query", "Stacks[0].Outputs",
            "--output", "json",
        ],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        sys.exit("Failed to describe CloudFormation stack. Check AWS credentials/region/stack name.")
    outputs = {o["OutputKey"]: o["OutputValue"] for o in json.loads(proc.stdout)}
    cluster_arn = cluster_arn or outputs.get("DBClusterArn")
    secret_arn = secret_arn or outputs.get("DBSecretArn")
    db_name = db_name or outputs.get("DBName")
    if not (cluster_arn and secret_arn and db_name):
        sys.exit(f"Missing DB outputs from stack {stack}: {outputs}")
    return {"region": region, "cluster_arn": cluster_arn, "secret_arn": secret_arn, "db_name": db_name}


def run_batch(env: dict, sql: str, param_sets: list, dry_run: bool) -> None:
    payload = {
        "resourceArn": env["cluster_arn"],
        "secretArn": env["secret_arn"],
        "database": env["db_name"],
        "sql": sql,
        "parameterSets": param_sets,
    }
    if dry_run:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        tmp_path = f.name
    try:
        proc = subprocess.run(
            [
                "aws", "rds-data", "batch-execute-statement",
                "--region", env["region"],
                "--cli-input-json", f"file://{tmp_path}",
            ],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            sys.exit(1)
    finally:
        os.unlink(tmp_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Build SQL/params but do not call AWS")
    parser.add_argument("--region", default=None)
    parser.add_argument("--only", default=None, help="Comma-separated table subset, e.g. faculty,faculty_education")
    args = parser.parse_args()

    if not PAYLOAD_DIR.exists():
        sys.exit(f"{PAYLOAD_DIR} not found. Run scripts/build_v1_migration_payload.py first.")

    env = resolve_env(args)
    print(f"Region: {env['region']}")
    print(f"DB: {env['db_name']}")
    print(f"Cluster ARN: {env['cluster_arn'][:40]}...redacted")

    only = set(args.only.split(",")) if args.only else None

    for table in INSERT_ORDER:
        if only and table not in only:
            continue
        rows_path = PAYLOAD_DIR / f"{table}.json"
        rows = json.loads(rows_path.read_text(encoding="utf-8"))
        if not rows:
            print(f"[{table}] 0 rows, skipping")
            continue
        spec = TABLE_SPECS[table]
        sql = build_sql(table, spec)
        columns = list(spec["columns"].keys())

        total = 0
        for chunk in chunked(rows, CHUNK_SIZE):
            param_sets = []
            for row in chunk:
                params = [
                    {"name": col, **build_param(row.get(col), spec["columns"][col])}
                    for col in columns
                ]
                param_sets.append(params)
            run_batch(env, sql, param_sets, args.dry_run)
            total += len(chunk)
        action = "would upsert" if args.dry_run else "upserted"
        print(f"[{table}] {action} {total} rows")

    print("Done." if not args.dry_run else "Dry run complete, no AWS calls made.")


if __name__ == "__main__":
    main()
