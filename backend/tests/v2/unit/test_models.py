"""Models must mirror database/migrations/002_lecturer_profile.sql (no database needed).

If you change the SQL, change the model too (and the other way round).
"""

import re
from pathlib import Path

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlmodel import SQLModel

import app.v2.models  # noqa: F401  (registers every table on SQLModel.metadata)

MIGRATION = Path(__file__).parents[4] / "database" / "migrations" / "002_lecturer_profile.sql"


def columns_in_migration() -> dict[str, set[str]]:
    sql = MIGRATION.read_text()
    tables: dict[str, set[str]] = {}
    for name, body in re.findall(r'CREATE TABLE "(\w+)" \((.*?)\n\);', sql, flags=re.S):
        tables[name] = set(re.findall(r'^\s*"(\w+)"', body, flags=re.M))
    return tables


def columns_in_models() -> dict[str, set[str]]:
    return {name: set(table.columns.keys()) for name, table in SQLModel.metadata.tables.items()}


def test_models_have_the_same_tables_and_columns_as_the_migration() -> None:
    assert columns_in_models() == columns_in_migration()


@pytest.mark.parametrize("table_name", sorted(columns_in_migration()))
def test_table_compiles_for_postgresql(table_name: str) -> None:
    table = SQLModel.metadata.tables[table_name]

    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))

    assert ddl.startswith(f"\nCREATE TABLE {table_name}")
