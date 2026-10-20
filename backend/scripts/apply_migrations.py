"""Apply database/migrations/*.sql that have not been applied yet, one transaction per file.

Aurora (private subnet, so through the RDS Data API; needs AWS credentials):

    cd backend
    uv run python -m scripts.apply_migrations --cluster-arn <arn> --secret-arn <arn> \
        --database cs361v2 --baseline 001_base     # 001 was applied by the V1 migration
    uv run python -m scripts.apply_migrations --cluster-arn <arn> --secret-arn <arn> \
        --database cs361v2

Any PostgreSQL you can reach directly:

    uv run python -m scripts.apply_migrations --database-url postgresql://postgres@localhost/cs361v2

Applied files are recorded in `schema_migration`. `--baseline NAME...` records files as
applied without running them (for a database that already has them). `--dry-run` only
lists what would run. The Data API takes one statement per call, so each file is split on
`;` outside quotes, comments and $$ bodies; the files' own BEGIN / COMMIT are dropped
because the script wraps every file in its own transaction.
"""

import argparse
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

MIGRATIONS = Path(__file__).resolve().parents[2] / "database" / "migrations"

TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migration (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
)
"""

_TRANSACTION_CONTROL = re.compile(r"^(BEGIN|COMMIT|START TRANSACTION|END)\s*$", re.IGNORECASE)
_DOLLAR_TAG = re.compile(r"\$[A-Za-z_]*\$")


def split_statements(sql: str) -> list[str]:
    """Split a SQL script into statements, keeping ; inside strings, comments and $$ bodies."""
    statements: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(sql):
        char = sql[i]
        if sql.startswith("--", i):
            end = sql.find("\n", i)
            i = len(sql) if end == -1 else end + 1
            current.append("\n")
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = len(sql) if end == -1 else end + 2
            continue
        if char == "'":
            end = i + 1
            while end < len(sql):
                if sql[end] == "'" and sql.startswith("''", end):
                    end += 2
                    continue
                if sql[end] == "'":
                    break
                end += 1
            current.append(sql[i : end + 1])
            i = end + 1
            continue
        if char == "$" and (tag := _DOLLAR_TAG.match(sql, i)):
            end = sql.find(tag.group(0), tag.end())
            end = len(sql) if end == -1 else end + len(tag.group(0))
            current.append(sql[i:end])
            i = end
            continue
        if char == ";":
            _finish(current, statements)
            current = []
        else:
            current.append(char)
        i += 1
    _finish(current, statements)
    return statements


def _finish(parts: list[str], statements: list[str]) -> None:
    statement = "".join(parts).strip()
    if statement and not _TRANSACTION_CONTROL.match(statement):
        statements.append(statement)


class Runner(Protocol):
    def applied(self) -> set[str]: ...

    def run_file(self, version: str, statements: list[str]) -> None:
        """Run the statements and record the version, all in one transaction."""

    def mark(self, version: str) -> None: ...


class PsycopgRunner:
    def __init__(self, url: str) -> None:
        import psycopg

        url = url.replace("postgresql+psycopg://", "postgresql://")
        # autocommit: every transaction() below is a real BEGIN / COMMIT, not a savepoint
        self.connection = psycopg.connect(url, autocommit=True)
        with self.connection.transaction():
            self.connection.execute(TRACKING_TABLE)

    def applied(self) -> set[str]:
        rows = self.connection.execute("SELECT version FROM schema_migration").fetchall()
        return {row[0] for row in rows}

    def run_file(self, version: str, statements: list[str]) -> None:
        with self.connection.transaction():
            for statement in statements:
                self.connection.execute(statement)
            self._record(version)

    def mark(self, version: str) -> None:
        with self.connection.transaction():
            self._record(version)

    def _record(self, version: str) -> None:
        self.connection.execute(
            "INSERT INTO schema_migration (version) VALUES (%s) ON CONFLICT DO NOTHING", (version,)
        )


class DataApiRunner:
    def __init__(self, cluster_arn: str, secret_arn: str, database: str, region: str) -> None:
        import boto3

        self.client = boto3.client("rds-data", region_name=region)
        self.target = {"resourceArn": cluster_arn, "secretArn": secret_arn, "database": database}
        self._execute(TRACKING_TABLE)

    def applied(self) -> set[str]:
        result = self._execute("SELECT version FROM schema_migration")
        return {record[0]["stringValue"] for record in result.get("records", [])}

    def run_file(self, version: str, statements: list[str]) -> None:
        transaction = self.client.begin_transaction(**self.target)["transactionId"]
        try:
            for statement in statements:
                self._execute(statement, transaction)
            self._record(version, transaction)
        except Exception:
            self.client.rollback_transaction(
                resourceArn=self.target["resourceArn"],
                secretArn=self.target["secretArn"],
                transactionId=transaction,
            )
            raise
        self.client.commit_transaction(
            resourceArn=self.target["resourceArn"],
            secretArn=self.target["secretArn"],
            transactionId=transaction,
        )

    def mark(self, version: str) -> None:
        self._record(version, None)

    def _record(self, version: str, transaction: str | None) -> None:
        self._execute(
            "INSERT INTO schema_migration (version) VALUES (:version) ON CONFLICT DO NOTHING",
            transaction,
            parameters=[{"name": "version", "value": {"stringValue": version}}],
        )

    def _execute(self, sql: str, transaction: str | None = None, **extra: object) -> dict:
        if transaction:
            extra["transactionId"] = transaction
        return self.client.execute_statement(**self.target, sql=sql, **extra)


def migration_files() -> Iterator[Path]:
    yield from sorted(MIGRATIONS.glob("*.sql"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--database-url", help="Direct connection, e.g. postgresql://...")
    target.add_argument("--cluster-arn", help="Aurora cluster ARN (RDS Data API)")
    parser.add_argument("--secret-arn", help="Secrets Manager ARN of the DB credential")
    parser.add_argument("--database", default="cs361v2")
    parser.add_argument("--region", default="ap-southeast-1")
    parser.add_argument(
        "--baseline",
        nargs="*",
        default=[],
        metavar="NAME",
        help="Record these files (e.g. 001_base) as applied without running",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.cluster_arn and not args.secret_arn:
        parser.error("--secret-arn is required with --cluster-arn")

    runner: Runner = (
        PsycopgRunner(args.database_url)
        if args.database_url
        else DataApiRunner(args.cluster_arn, args.secret_arn, args.database, args.region)
    )

    applied = runner.applied()
    for name in args.baseline:
        if name not in applied:
            print(f"baseline  {name}" + (" (dry run)" if args.dry_run else ""))
            if not args.dry_run:
                runner.mark(name)
            applied.add(name)

    pending = [path for path in migration_files() if path.stem not in applied]
    if not pending:
        print("Nothing to apply")
    for path in pending:
        statements = split_statements(path.read_text(encoding="utf-8"))
        print(
            f"apply     {path.stem} ({len(statements)} statements)"
            + (" (dry run)" if args.dry_run else "")
        )
        if not args.dry_run:
            runner.run_file(path.stem, statements)


if __name__ == "__main__":
    main()
