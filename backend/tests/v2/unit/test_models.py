"""Models must mirror database/migrations/ 002 + 003 (no database needed).

If you change the SQL, change the model too (and the other way round).
"""

import re
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel

import app.v2.models  # noqa: F401  (registers every table on SQLModel.metadata)

MIGRATIONS_DIR = Path(__file__).parents[4] / "database" / "migrations"
# 001_base.sql is the old V2 baseline; the models start at 002.
MIGRATIONS = [
    MIGRATIONS_DIR / "002_lecturer_profile.sql",
    MIGRATIONS_DIR / "003_faculty_workload.sql",
]


def migration_sql() -> str:
    return "\n".join(path.read_text() for path in MIGRATIONS)


def columns_in_migration() -> dict[str, set[str]]:
    sql = migration_sql()
    tables: dict[str, set[str]] = {}
    for name, body in re.findall(r'CREATE TABLE "(\w+)" \((.*?)\n\);', sql, flags=re.S):
        tables[name] = set(re.findall(r'^\s*"(\w+)"', body, flags=re.M))
    for name, column in re.findall(r'ALTER TABLE "(\w+)" ADD COLUMN "(\w+)"', sql):
        tables[name].add(column)
    return tables


def enums_in_migration() -> dict[str, list[str]]:
    return {
        name: re.findall(r"'(\w+)'", values)
        for name, values in re.findall(
            r'CREATE TYPE "(\w+)" AS ENUM \((.*?)\);', migration_sql(), flags=re.S
        )
    }


def columns_in_models() -> dict[str, set[str]]:
    return {name: set(table.columns.keys()) for name, table in SQLModel.metadata.tables.items()}


def enums_in_models() -> dict[str, list[str]]:
    return {
        column.type.name: list(column.type.enums)
        for table in SQLModel.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, sa.Enum)
    }


def test_models_have_the_same_tables_and_columns_as_the_migration() -> None:
    assert columns_in_models() == columns_in_migration()


def test_models_have_the_same_enum_types_and_values_as_the_migration() -> None:
    assert enums_in_models() == enums_in_migration()


@pytest.mark.parametrize("table_name", sorted(columns_in_migration()))
def test_table_compiles_for_postgresql(table_name: str) -> None:
    table = SQLModel.metadata.tables[table_name]

    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))

    assert ddl.startswith(f"\nCREATE TABLE {table_name}")
