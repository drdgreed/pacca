"""
PACCA FastAPI Application.

Main entry point for the Prior Authorization & Care Coordination
Agent Platform REST API.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pacca import __version__
from pacca.api.routes import authorizations, health
from pacca.config import get_logger, get_settings, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    setup_logging()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )

    # Initialize resources (database, cache, etc.)
    # In production, this would initialize:
    # - Database connection pool
    # - Redis connection
    # - Vector store client

    yield

    # Shutdown
    logger.info("application_shutting_down")
    # Clean up resources


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="PACCA API",
        description=(
            "Prior Authorization & Care Coordination Agent Platform API. "
            "A multi-agent AI system for healthcare prior authorization workflows."
        ),
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start_time = datetime.utcnow()
        request_id = request.headers.get("X-Request-ID", str(datetime.utcnow().timestamp()))

        # Add request context for logging
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))

        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions."""
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "detail": str(exc) if settings.debug else None,
            },
        )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(authorizations.router, prefix="/api/v1", tags=["Authorizations"])

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "pacca.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
