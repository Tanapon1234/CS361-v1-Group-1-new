"""Recognise PostgreSQL constraint errors that services turn into 409 / 400."""

from sqlalchemy.exc import IntegrityError


def _sqlstate(exc: IntegrityError) -> str | None:
    return getattr(exc.orig, "sqlstate", None) or getattr(exc.orig, "pgcode", None)


def is_unique_violation(exc: IntegrityError) -> bool:
    return _sqlstate(exc) == "23505" or "unique constraint failed" in str(exc.orig).lower()


def is_foreign_key_violation(exc: IntegrityError) -> bool:
    return _sqlstate(exc) == "23503" or "foreign key constraint failed" in str(exc.orig).lower()
