"""FastAPI application. Run with `fastapi dev` (entrypoint is set in pyproject.toml)."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.core import health
from app.core.config import get_settings
from app.core.database import dispose_engine
from app.core.error_handlers import register_exception_handlers
from app.v2.router import api_v2_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    dispose_engine()


def _operation_id(route: APIRoute) -> str:
    # Clean OpenAPI operationIds (e.g. `create_lecturer`) for frontend client generators.
    return route.name


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    docs_enabled = not settings.is_production

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        generate_unique_id_function=_operation_id,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(api_v2_router)
    return app


app = create_app()
