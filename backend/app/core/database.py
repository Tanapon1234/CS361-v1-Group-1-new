"""Database engine and the per-request session (unit of work)."""

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, event
from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.core.db_secret import IamTokenCredentials, SecretCredentials


@lru_cache
def get_engine() -> Engine:
    """Create the engine lazily so importing the app never opens a DB connection."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
    )
    credentials: SecretCredentials | IamTokenCredentials | None = None
    if settings.db_iam_auth:
        credentials = IamTokenCredentials(
            settings.db_host, settings.db_port, settings.db_user, settings.aws_region
        )
    elif settings.db_secret_arn:
        credentials = SecretCredentials(
            settings.db_secret_arn, settings.aws_region, settings.db_secret_cache_seconds
        )
    if credentials is not None:

        @event.listens_for(engine, "do_connect")
        def _use_credentials(dialect, conn_rec, cargs, cparams) -> None:
            cparams.update(credentials.connect_params())

    return engine


def get_session() -> Iterator[Session]:
    """Yield one session wrapped in one transaction per request.

    Commits when the path operation returns normally and rolls back on any exception,
    so DAOs only `add` / `flush` and never commit on their own.
    Always inject it through `SessionDep` below.
    """
    with Session(get_engine()) as session, session.begin():
        yield session


# scope="function": commit/rollback runs *before* the response is sent to the client.
SessionDep = Annotated[Session, Depends(get_session, scope="function")]


def dispose_engine() -> None:
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()
