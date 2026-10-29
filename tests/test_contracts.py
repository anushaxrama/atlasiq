from datetime import datetime

import httpx
import pytest

from atlasiq import sources
from atlasiq.operations import months


def row():
    return dict(
        pickup_at=datetime(2025, 1, 2, 10),
        dropoff_at=datetime(2025, 1, 2, 10, 20),
        distance_miles=3,
        fare_usd=14,
        total_usd=20,
        pickup_zone=1,
        dropoff_zone=2,
        passenger_count=1,
    )


@pytest.mark.parametrize("month", ["2025-00", "2025-13", "x", "2025-1", "2025-01';DROP TABLE x"])
def test_month_contract(month):
    with pytest.raises(ValueError):
        sources.month_date(month)


def test_backfill_crosses_year_and_rejects_reverse():
    assert months("2024-12", "2025-02") == ["2024-12", "2025-01", "2025-02"]
    with pytest.raises(ValueError):
        months("2025-02", "2025-01")


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("actual_unused", None, None),
        ("fare_usd", -1, "invalid_fare_usd"),
        ("distance_miles", float("nan"), "invalid_distance_miles"),
        ("total_usd", float("inf"), "invalid_total_usd"),
        ("pickup_zone", 999, "unknown_zone"),
        ("passenger_count", 10, "invalid_passenger_count"),
        ("passenger_count", None, None),
        ("pickup_at", None, "missing_timestamp"),
        ("dropoff_at", datetime(2025, 1, 2, 9), "duration_outside_0_360_minutes"),
    ],
)
def test_domain_validation(field, value, reason):
    item = row()
    item[field] = value
    assert sources.validate_trip(item, "2025-01", {1, 2}) == reason


def test_schema_change_and_forward_compatible_columns():
    with pytest.raises(ValueError, match="Schema drift"):
        sources.check_trip_schema({"VendorID"})
    assert "cbd_congestion_fee" in sources.check_trip_schema(
        sources.REQUIRED_TRIP_FIELDS | {"cbd_congestion_fee"}
    )


def client_patch(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(
        sources.httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler))
    )
    monkeypatch.setattr(sources.time, "sleep", lambda seconds: None)


def test_http_retries_rate_limits_and_retains_checksum(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA", tmp_path)
    calls = []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "0"})
            if len(calls) == 1
            else httpx.Response(200, content=b"a,b\n1,2", headers={"content-type": "text/csv"})
        )

    client_patch(monkeypatch, handler)
    file = sources.download("test fixture", "https://example.test/file", "csv")
    assert len(calls) == 2
    assert sources.checksum(file.path) == file.sha256
    assert sources.download("test fixture", file.url, "csv").sha256 == file.sha256
    assert len(calls) == 2
    file.path.write_text("corrupt")
    with pytest.raises(ValueError, match="checksum mismatch"):
        sources.download("test fixture", file.url, "csv")


def test_missing_partition_is_not_retried(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA", tmp_path)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(404)

    client_patch(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        sources.download("test", "https://example.test/missing", "parquet")
    assert len(calls) == 1


def test_source_unavailable_has_bounded_attempts(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA", tmp_path)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503)

    client_patch(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        sources.download("test", "https://example.test/unavailable", "parquet")
    assert len(calls) == 4
    assert not list(tmp_path.rglob("*.part"))


def test_rejects_html_response(monkeypatch, tmp_path):
    monkeypatch.setattr(sources, "DATA", tmp_path)
    client_patch(
        monkeypatch,
        lambda request: httpx.Response(
            200, text="<html>Error</html>", headers={"content-type": "text/html"}
        ),
    )
    with pytest.raises(ValueError, match="content type"):
        sources.download("test", "https://example.test/file", "parquet")


def test_source_type_drift_is_explicit():
    schema = {name: "INTEGER" for name in sources.REQUIRED_TRIP_FIELDS}
    schema["tpep_pickup_datetime"] = schema["tpep_dropoff_datetime"] = "TIMESTAMP"
    sources.check_trip_types(schema)
    schema["fare_amount"] = "VARCHAR"
    with pytest.raises(ValueError, match="must be numeric"):
        sources.check_trip_types(schema)
    schema["fare_amount"] = "DOUBLE"
    schema["tpep_pickup_datetime"] = "BIGINT"
    with pytest.raises(ValueError, match="must be a timestamp"):
        sources.check_trip_types(schema)
