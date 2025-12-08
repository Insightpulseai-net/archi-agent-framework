"""
Tenant Middleware
=================
Multi-tenant context management.
"""

from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for multi-tenant context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract tenant from various sources
        tenant_id = self._extract_tenant_id(request)

        if not tenant_id:
            tenant_id = settings.DEFAULT_TENANT_ID

        # Store in request state
        request.state.tenant_id = tenant_id

        # Log tenant context
        logger.debug(
            "Tenant context set",
            tenant_id=tenant_id,
            path=request.url.path,
        )

        # Process request
        response = await call_next(request)

        return response

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request."""
        # Try X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # Try subdomain (tenant.workbench.insightpulseai.net)
        host = request.headers.get("host", "")
        if host and "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["workbench", "www", "api"]:
                return subdomain

        # Try query parameter (for development)
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        return None
