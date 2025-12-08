"""
Data Engineering Workbench - Main Application
=============================================
FastAPI application entry point for the Data Engineering Workbench.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis
from app.api.v1.router import api_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.tenant import TenantMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Data Engineering Workbench", version=settings.APP_VERSION)

    await init_db()
    await init_redis()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")

    await close_db()
    await close_redis()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Data Engineering Workbench",
    description="""
    A Databricks-style data engineering platform for the InsightPulseAI ecosystem.

    ## Features

    * **Notebooks**: Interactive SQL and Python notebook environment
    * **Pipelines**: Orchestrated data transformation workflows
    * **Data Catalog**: Discover and document your data assets
    * **Connections**: Manage connections to Odoo, Superset, OCR, and more
    * **Medallion Architecture**: Bronze → Silver → Gold data layers

    ## Authentication

    All endpoints require authentication via JWT token in the Authorization header:
    ```
    Authorization: Bearer <token>
    ```
    """,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
if settings.MULTI_TENANT_ENABLED:
    app.add_middleware(TenantMiddleware)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# Readiness check endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check that verifies all dependencies are available.
    """
    from app.core.database import check_db_connection
    from app.core.redis import check_redis_connection

    checks = {
        "database": await check_db_connection(),
        "redis": await check_redis_connection(),
    }

    all_healthy = all(checks.values())

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
        }
    )


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
