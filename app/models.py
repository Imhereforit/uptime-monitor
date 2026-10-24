"""Request/response schemas with validation.

Pydantic validates every field at the system boundary before our code touches it.
Rejecting malformed or malicious input early is a fundamental security practice.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class TargetIn(BaseModel):
    """A URL the caller wants us to monitor."""

    # HttpUrl enforces a valid http/https URL — this blocks things like
    # file:// or javascript: schemes that could be abused (SSRF-style input).
    url: HttpUrl
    name: str = Field(min_length=1, max_length=100)


class CheckResult(BaseModel):
    """The outcome of a single uptime check."""

    name: str
    url: str
    is_up: bool
    status_code: int | None = None
    latency_ms: float | None = None
    error: str | None = None
