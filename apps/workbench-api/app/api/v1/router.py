"""
API Router
==========
Main API router that combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    notebooks,
    pipelines,
    connections,
    catalog,
    executions,
    integrations,
)

api_router = APIRouter()

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Notebooks
api_router.include_router(
    notebooks.router,
    prefix="/notebooks",
    tags=["Notebooks"],
)

# Pipelines
api_router.include_router(
    pipelines.router,
    prefix="/pipelines",
    tags=["Pipelines"],
)

# Connections
api_router.include_router(
    connections.router,
    prefix="/connections",
    tags=["Connections"],
)

# Data Catalog
api_router.include_router(
    catalog.router,
    prefix="/catalog",
    tags=["Data Catalog"],
)

# Executions (cell execution, query execution)
api_router.include_router(
    executions.router,
    prefix="/execute",
    tags=["Execution"],
)

# External Integrations
api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["Integrations"],
)
