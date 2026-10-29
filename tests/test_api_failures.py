import psycopg
from fastapi.testclient import TestClient

from atlasiq import api


def test_unavailable_database_returns_helpful_503(monkeypatch):
    def fail(*args, **kwargs):
        raise psycopg.OperationalError("test outage")

    monkeypatch.setattr(api, "query", fail)
    response = TestClient(api.app).get("/api/summary")
    assert response.status_code == 503
    assert "Warehouse unavailable" in response.json()["detail"]
    assert "test outage" not in response.text


def test_invalid_dates_and_excessive_bounds():
    client = TestClient(api.app)
    for path in [
        "/api/summary?start=nonsense",
        "/api/trends?start=2020-01-01&end=2025-01-01",
        "/api/runs?limit=101",
        "/api/quality?offset=-1",
    ]:
        assert client.get(path).status_code == 422


def test_unpublished_partition_blocks_metrics_but_operations_remain_available(monkeypatch):
    def unpublished(sql, params=None):
        if "count(*) filter" in sql:
            return [{"total": 1, "published": 0}]
        return []

    monkeypatch.setattr(api, "query", unpublished)
    client = TestClient(api.app)
    assert client.get("/api/summary").status_code == 503
    assert "not published" in client.get("/api/meta").json()["detail"]
    assert client.get("/api/runs").status_code == 200
