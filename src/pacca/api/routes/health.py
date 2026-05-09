"""
Health check endpoints.

Provides endpoints for monitoring application health and readiness.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from pacca import __version__
from pacca.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: dict[str, Any] = Field(default_factory=dict, description="Individual health checks")


class MetricsResponse(BaseModel):
    """Basic metrics response model."""

    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    requests_total: int = Field(0, description="Total requests processed")
    authorizations_processed: int = Field(0, description="Total authorizations processed")
    autonomous_decisions: int = Field(0, description="Decisions made autonomously")
    escalated_decisions: int = Field(0, description="Decisions escalated to human review")
    average_processing_time_ms: float = Field(0.0, description="Average processing time")


# Track application start time for uptime calculation
_start_time = datetime.utcnow()

# In-memory metrics (would use Redis or DB in production)
_metrics = {
    "requests_total": 0,
    "authorizations_processed": 0,
    "autonomous_decisions": 0,
    "escalated_decisions": 0,
    "total_processing_time_ms": 0.0,
}


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the application and its dependencies.",
)
async def health_check() -> HealthResponse:
    """
    Perform health check on the application.

    Returns:
        HealthResponse with overall status and individual component checks
    """
    settings = get_settings()
    checks: dict[str, Any] = {}

    # Check LLM availability (basic check)
    checks["llm"] = {
        "status": "healthy",
        "model": settings.default_model,
    }

    # Check configuration
    checks["config"] = {
        "status": "healthy",
        "autonomous_decisions_enabled": settings.enable_autonomous_decisions,
        "rag_enabled": settings.enable_rag,
        "demo_mode": settings.demo_mode,
    }

    # In production, would also check:
    # - Database connectivity
    # - Redis connectivity
    # - Vector store availability
    # - External API health

    # Determine overall status
    all_healthy = all(check.get("status") == "healthy" for check in checks.values())
    overall_status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        environment=settings.app_env,
        checks=checks,
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the application is ready to accept traffic.",
)
async def readiness_check() -> dict[str, str]:
    """
    Kubernetes-style readiness probe.

    Returns 200 if ready, 503 if not ready.
    """
    # In production, this would check:
    # - Database connection is established
    # - Required services are available
    # - Application has finished initialization

    return {"status": "ready"}


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the application is alive (not deadlocked).",
)
async def liveness_check() -> dict[str, str]:
    """
    Kubernetes-style liveness probe.

    Returns 200 if alive, used to detect deadlocks.
    """
    return {"status": "alive"}


@router.get(
    "/api/v1/metrics",
    response_model=MetricsResponse,
    summary="Application Metrics",
    description="Get basic application metrics.",
)
async def get_metrics() -> MetricsResponse:
    """
    Get application metrics.

    Returns:
        MetricsResponse with current metrics
    """
    settings = get_settings()

    if not settings.metrics_enabled:
        return MetricsResponse(uptime_seconds=0)

    uptime = (datetime.utcnow() - _start_time).total_seconds()

    avg_time = 0.0
    if _metrics["authorizations_processed"] > 0:
        avg_time = _metrics["total_processing_time_ms"] / _metrics["authorizations_processed"]

    return MetricsResponse(
        uptime_seconds=uptime,
        requests_total=_metrics["requests_total"],
        authorizations_processed=_metrics["authorizations_processed"],
        autonomous_decisions=_metrics["autonomous_decisions"],
        escalated_decisions=_metrics["escalated_decisions"],
        average_processing_time_ms=avg_time,
    )


def record_authorization_metrics(
    processing_time_ms: float,
    was_autonomous: bool,
) -> None:
    """
    Record metrics for a processed authorization.

    This would typically be called from the authorization processing flow.
    """
    _metrics["authorizations_processed"] += 1
    _metrics["total_processing_time_ms"] += processing_time_ms

    if was_autonomous:
        _metrics["autonomous_decisions"] += 1
    else:
        _metrics["escalated_decisions"] += 1


def increment_request_count() -> None:
    """Increment the total request counter."""
    _metrics["requests_total"] += 1
