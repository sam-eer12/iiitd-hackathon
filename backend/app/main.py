"""FastAPI application factory, routers, lifespan, and error handling."""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    bookmarks,
    evidence,
    health,
    imports,
    me,
    profiles,
    refreshes,
    sources,
    tenders,
)
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, http_exception_handler
from app.core.logging import get_logger, setup_logging
from app.database import async_session_factory
from app.repositories.sources import upsert_source
from app.sources.iiitd import APPROVED_HOSTS, SOURCE_ID, SOURCE_NAME, START_URL

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting TenderLens Backend (env: %s)", settings.APP_ENV)

    # Seed default source 'iiitd' if missing
    try:
        async with async_session_factory() as db:
            await upsert_source(
                db,
                source_id=SOURCE_ID,
                name=SOURCE_NAME,
                start_url=START_URL,
                approved_hosts=APPROVED_HOSTS,
            )
            logger.info("Default source '%s' initialized.", SOURCE_ID)
    except Exception as exc:
        logger.warning("Could not auto-seed default source at startup: %s", exc)

    yield
    logger.info("Shutting down TenderLens Backend")


def create_app() -> FastAPI:
    get_settings()
    app = FastAPI(
        title="TenderLens Backend API",
        description="Evidence-backed government tender discovery and readiness evaluation platform.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and timing middleware
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-Id", f"req_{uuid.uuid4().hex[:8]}")
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response

    # Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Health & Readiness (root level)
    app.include_router(health.router)

    # API v1 routes
    api_v1_prefix = "/api/v1"
    app.include_router(me.router, prefix=api_v1_prefix)
    app.include_router(profiles.router, prefix=api_v1_prefix)
    app.include_router(bookmarks.router, prefix=api_v1_prefix)
    app.include_router(sources.router, prefix=api_v1_prefix)
    app.include_router(refreshes.router, prefix=api_v1_prefix)
    app.include_router(tenders.router, prefix=api_v1_prefix)
    app.include_router(evidence.router, prefix=api_v1_prefix)
    app.include_router(imports.router, prefix=api_v1_prefix)

    return app


app = create_app()
