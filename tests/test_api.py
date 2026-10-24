"""API tests using FastAPI's TestClient. Follows Arrange-Act-Assert."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import _targets, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    """Each test starts with an empty target store (test isolation)."""
    _targets.clear()
    yield
    _targets.clear()


def test_healthz_reports_alive():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readyz_reports_ready():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_endpoint_exposes_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "uptime_checks_total" in response.text


def test_add_and_list_target():
    # Arrange / Act
    response = client.post(
        "/targets", json={"name": "example", "url": "https://example.com"}
    )
    # Assert
    assert response.status_code == 201
    assert client.get("/targets").json() == {"example": "https://example.com/"}


def test_rejects_invalid_url():
    response = client.post("/targets", json={"name": "bad", "url": "not-a-url"})
    assert response.status_code == 422  # validation error, request never reaches logic


def test_rejects_empty_name():
    response = client.post("/targets", json={"name": "", "url": "https://example.com"})
    assert response.status_code == 422


def test_delete_unknown_target_returns_404():
    response = client.delete("/targets/does-not-exist")
    assert response.status_code == 404


def test_check_unknown_target_returns_404():
    response = client.post("/check/does-not-exist")
    assert response.status_code == 404
