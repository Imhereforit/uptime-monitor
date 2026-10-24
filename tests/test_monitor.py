"""Unit tests for the monitoring logic, using a mocked HTTP transport.

We never hit the real network in tests — that keeps tests fast, deterministic,
and runnable offline (a CI best practice).
"""

from __future__ import annotations

import httpx
import pytest

from app.monitor import check_target


@pytest.mark.asyncio
async def test_target_is_up_on_200(monkeypatch):
    async def fake_get(self, url):  # noqa: ANN001
        return httpx.Response(200, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await check_target("example", "https://example.com", timeout_seconds=1.0)

    assert result.is_up is True
    assert result.status_code == 200
    assert result.error is None


@pytest.mark.asyncio
async def test_target_is_down_on_500(monkeypatch):
    async def fake_get(self, url):  # noqa: ANN001
        return httpx.Response(500, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await check_target("example", "https://example.com", timeout_seconds=1.0)

    assert result.is_up is False
    assert result.status_code == 500


@pytest.mark.asyncio
async def test_target_is_down_on_connection_error(monkeypatch):
    async def fake_get(self, url):  # noqa: ANN001
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = await check_target("example", "https://example.com", timeout_seconds=1.0)

    assert result.is_up is False
    assert result.error == "ConnectError"
