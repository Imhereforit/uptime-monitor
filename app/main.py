"""FastAPI application entrypoint.

Exposes:
  - CRUD-ish endpoints to register and check monitored targets
  - /healthz  liveness probe   (is the process alive?)
  - /readyz   readiness probe  (is the app ready to serve traffic?)
  - /metrics  Prometheus metrics (SLIs for dashboards and alerts)

Liveness vs readiness is the standard Kubernetes/ECS health-check split and is a
signal that you understand how orchestrators manage containers.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from . import __version__
from .config import settings
from .logging_config import configure_logging
from .models import CheckResult, TargetIn
from .monitor import check_target

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version=__version__)

# In-memory store. A real service would use a database; keeping it in memory
# makes the project runnable with zero external dependencies.
_targets: dict[str, str] = {}

# --- Prometheus metrics (these become your SLIs) ---------------------------
CHECKS_TOTAL = Counter(
    "uptime_checks_total",
    "Total uptime checks performed.",
    labelnames=("target", "result"),
)
CHECK_LATENCY = Histogram(
    "uptime_check_latency_seconds",
    "Latency of uptime checks in seconds.",
    labelnames=("target",),
)


@app.get("/healthz")
def liveness() -> dict[str, str]:
    """Liveness probe: the process is running."""
    return {"status": "alive"}


@app.get("/readyz")
def readiness() -> dict[str, str]:
    """Readiness probe: the app is ready to accept work."""
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    """Expose metrics in the Prometheus text format."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/targets")
def list_targets() -> dict[str, str]:
    return _targets


@app.post("/targets", status_code=status.HTTP_201_CREATED)
def add_target(target: TargetIn) -> dict[str, str]:
    if len(_targets) >= settings.max_targets and target.name not in _targets:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Target limit of {settings.max_targets} reached.",
        )
    _targets[target.name] = str(target.url)
    logger.info("registered target", extra={"target": target.name})
    return {"name": target.name, "url": str(target.url)}


@app.delete("/targets/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(name: str) -> Response:
    if name not in _targets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown target.")
    del _targets[name]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/check/{name}")
async def check_one(name: str) -> CheckResult:
    url = _targets.get(name)
    if url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown target.")

    result = await check_target(name, url, settings.request_timeout_seconds)

    CHECKS_TOTAL.labels(target=name, result="up" if result.is_up else "down").inc()
    if result.latency_ms is not None:
        CHECK_LATENCY.labels(target=name).observe(result.latency_ms / 1000)

    return result
