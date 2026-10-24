"""Configuration loaded from environment variables.

Secrets and environment-specific values never live in source code. They are read
from the environment at startup, which is the standard pattern for containers and
cloud platforms (12-factor app, config).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable application settings, populated from the environment."""

    app_name: str
    log_level: str
    request_timeout_seconds: float
    max_targets: int

    @staticmethod
    def from_env() -> Settings:
        return Settings(
            app_name=os.getenv("APP_NAME", "uptime-monitor"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5.0")),
            max_targets=int(os.getenv("MAX_TARGETS", "50")),
        )


settings = Settings.from_env()
