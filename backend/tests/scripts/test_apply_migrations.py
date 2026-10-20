"""The Data API takes one statement per call, so migrations are split client-side."""

import pytest

from scripts.apply_migrations import migration_files, split_statements


def test_splits_on_semicolons_outside_quotes_and_comments() -> None:
    sql = """
    BEGIN;
    -- a comment; with a semicolon
    CREATE TABLE a (note text DEFAULT 'x;y', other text DEFAULT 'it''s; fine');
    /* block; comment */ INSERT INTO a VALUES ('1');
    COMMIT;
    """

    assert split_statements(sql) == [
        "CREATE TABLE a (note text DEFAULT 'x;y', other text DEFAULT 'it''s; fine')",
        "INSERT INTO a VALUES ('1')",
    ]


def test_keeps_a_dollar_quoted_function_body_whole() -> None:
    sql = """
    CREATE FUNCTION f() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
      RETURN NEW;
    END;
    $$;
    CREATE TRIGGER t BEFORE INSERT ON a FOR EACH ROW EXECUTE FUNCTION f();
    """

    statements = split_statements(sql)

    assert len(statements) == 2
    assert statements[0].endswith("$$")
    assert "RETURN OLD; END IF;" in statements[0]


@pytest.mark.parametrize("path", list(migration_files()), ids=lambda path: path.stem)
def test_every_migration_splits_into_complete_statements(path) -> None:
    statements = split_statements(path.read_text(encoding="utf-8"))

    assert statements
    for statement in statements:
        assert statement.upper() not in {"BEGIN", "COMMIT"}
        assert statement.count("$$") % 2 == 0
