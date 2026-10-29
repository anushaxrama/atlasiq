"""Synthetic fixtures only. Requires an explicitly separate disposable PostgreSQL test DB."""

import os
from datetime import datetime, timezone

import duckdb
import pytest
from fastapi.testclient import TestClient

from atlasiq import config, db, ingest, sources
from atlasiq.api import app
from atlasiq.operations import dbt, publish


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    url = os.getenv("TEST_ATLAS_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_ATLAS_DATABASE_URL to a disposable test database")
    if url == config.DATABASE_URL or not url.rstrip("/").endswith("atlasiq_test"):
        raise RuntimeError("Refusing to modify a non-test database")
    original_db, original_config = db.DATABASE_URL, config.DATABASE_URL
    db.DATABASE_URL = config.DATABASE_URL = url
    with db.connection() as conn:
        for schema in ["marts", "intermediate", "staging", "raw"]:
            conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    folder = tmp_path_factory.mktemp("fixtures")
    zones = folder / "zones.csv"
    zones.write_text(
        "LocationID,Borough,Zone,service_zone\n1,Test borough,Fixture zone A,Yellow Zone\n2,Test borough,Fixture zone B,Yellow Zone\n"
    )
    weather = folder / "weather.csv"
    weather.write_text(
        "STATION,DATE,TEMP,PRCP\nFIXTURE,2025-01-02,32,0.1\nFIXTURE,2025-01-03,9999.9,99.99\n"
    )
    parquet = folder / "trips.parquet"
    c = duckdb.connect()
    c.execute("""create table trips as select 1 as VendorID,timestamp '2025-01-02 10:00:00'+ i*interval '1 minute' as tpep_pickup_datetime,
    timestamp '2025-01-02 10:15:00'+i*interval '1 minute' as tpep_dropoff_datetime,1 as PULocationID,2 as DOLocationID,
    1.0 as passenger_count,3.0 as trip_distance,15.0 as fare_amount,20.0 as total_amount,1 as payment_type from range(30) t(i)""")
    c.execute("insert into trips select * from trips limit 1")
    c.execute(
        "insert into trips select VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,PULocationID,DOLocationID,passenger_count,trip_distance,-10,total_amount,payment_type from trips limit 1"
    )
    c.execute("copy trips to ? (format parquet)", [str(parquet)])
    c.close()
    original = ingest.download

    def local(source, url, extension, refresh=False):
        p = parquet if extension == "parquet" else weather if "noaa" in url else zones
        return sources.LandedFile(
            source,
            url,
            p,
            sources.checksum(p),
            p.stat().st_size,
            "application/octet-stream",
            datetime.now(timezone.utc).isoformat(),
        )

    ingest.download = local
    yield parquet
    ingest.download = original
    db.DATABASE_URL = original_db
    config.DATABASE_URL = original_config


def test_duplicate_rerun_quarantine_and_partial_recovery(warehouse):
    first = ingest.ingest("2025-01", 0)
    assert (first["accepted"], first["rejected"], first["duplicates"]) == (30, 1, 1)
    second = ingest.ingest("2025-01", 0)
    assert second["accepted"] == 30
    assert db.query("select count(*) as n from raw.trips")[0]["n"] == 30
    assert db.query("select count(*) as n from raw.quarantine")[0]["n"] == 2
    before = db.query("select trip_id from raw.trips order by trip_id")
    with pytest.raises(RuntimeError, match="Injected"):
        ingest.ingest("2025-01", 0, fail_after=5)
    assert db.query("select trip_id from raw.trips order by trip_id") == before
    assert (
        db.query("select status from raw.ingestion_runs order by started_at desc limit 1")[0][
            "status"
        ]
        == "failed"
    )


def test_dbt_incremental_replay_and_api(warehouse):
    dbt()
    publish()
    assert db.query("select count(*) as n from marts.fct_trips")[0]["n"] == 30
    ingest.ingest("2025-01", 0)
    dbt()
    publish()
    assert db.query("select count(*) as n from marts.fct_trips")[0]["n"] == 30
    client = TestClient(app)
    assert client.get("/api/summary").json()["observed_trips"] == 30
    assert client.get("/api/zones?zone=1").json()[0]["zone_name"] == "Fixture zone A"
    for path in ["trends", "hourly", "weather", "anomalies", "quality", "runs", "meta"]:
        assert client.get("/api/" + path).status_code == 200
    assert client.get("/api/summary?zone=999").status_code == 422
    assert client.get("/api/summary?start=2025-02-01&end=2025-01-01").status_code == 422
    assert client.get("/api/zones?limit=10000").status_code == 422
    assert client.get("/api/summary?zone=1%3BDROP%20TABLE%20raw.trips").status_code == 422
    assert client.get("/api/summary?start=2026-01-01&end=2026-01-02").json()["observed_trips"] == 0
    assert client.get("/ready").status_code == 200


def test_corrupted_parquet_and_schema_drift_preserve_previous_partition(warehouse):
    before = db.query("select count(*) as n from raw.trips")[0]["n"]
    original = warehouse.read_bytes()
    try:
        warehouse.write_bytes(b"corrupted parquet fixture")
        with pytest.raises(duckdb.Error):
            ingest.ingest("2025-01", 0)
        assert db.query("select count(*) as n from raw.trips")[0]["n"] == before
        warehouse.unlink()
        c = duckdb.connect()
        c.execute("copy (select 1 as unexpected) to ? (format parquet)", [str(warehouse)])
        c.close()
        with pytest.raises(ValueError, match="Schema drift"):
            ingest.ingest("2025-01", 0)
        assert db.query("select count(*) as n from raw.trips")[0]["n"] == before
    finally:
        warehouse.write_bytes(original)


def test_revised_partition_removes_old_facts(warehouse):
    original = warehouse.read_bytes()
    c = duckdb.connect()
    c.read_parquet(str(warehouse)).create_view("original")
    reduced = warehouse.with_name("revised.parquet")
    c.execute(
        "copy (select * from original where tpep_pickup_datetime >= timestamp '2025-01-02 10:10:00') to ? (format parquet)",
        [str(reduced)],
    )
    c.close()
    try:
        warehouse.write_bytes(reduced.read_bytes())
        result = ingest.ingest("2025-01", 0)
        assert result["accepted"] == 20
        dbt()
        publish()
        assert db.query("select count(*) as n from marts.fct_trips")[0]["n"] == 20
        assert (
            db.query(
                "select count(*) as n from marts.fct_trips where pickup_at < timestamp '2025-01-02 10:10:00'"
            )[0]["n"]
            == 0
        )
    finally:
        warehouse.write_bytes(original)
