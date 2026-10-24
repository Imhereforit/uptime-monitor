"""Core uptime-checking logic, kept separate from the web layer so it is easy to test."""

from __future__ import annotations

import logging
import time

import httpx

from .models import CheckResult

logger = logging.getLogger(__name__)


async def check_target(
    name: str, url: str, timeout_seconds: float
) -> CheckResult:
    """Perform a single HTTP GET and report whether the target is up.

    "Up" means we got any HTTP response with a status below 400. Timeouts,
    DNS failures and connection errors all count as down.
    """
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(url)
        latency_ms = (time.perf_counter() - start) * 1000
        is_up = response.status_code < 400
        logger.info(
            "checked target",
            extra={"target": name, "status_code": response.status_code, "is_up": is_up},
        )
        return CheckResult(
            name=name,
            url=url,
            is_up=is_up,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
        )
    except httpx.HTTPError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "target check failed",
            extra={"target": name, "error": str(exc)},
        )
        return CheckResult(
            name=name,
            url=url,
            is_up=False,
            latency_ms=round(latency_ms, 2),
            error=type(exc).__name__,
        )
