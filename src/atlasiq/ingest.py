"""Audited extraction and atomic partition replacement; dbt owns business transformations."""

import csv
import json
import logging
import time
import uuid
from typing import Any

import duckdb
from psycopg.types.json import Jsonb

from .db import bootstrap, connection
from .sources import (
    LandedFile,
    check_trip_schema,
    check_trip_types,
    download,
    month_date,
    validate_trip,
)

logger = logging.getLogger("atlasiq")
TRIP_COLUMNS = [
    "partition_month",
    "trip_id",
    "pickup_at",
    "dropoff_at",
    "pickup_zone",
    "dropoff_zone",
    "vendor_id",
    "passenger_count",
    "distance_miles",
    "fare_usd",
    "total_usd",
    "payment_type",
    "source_hash",
    "run_id",
]


def register_file(conn: Any, file: LandedFile) -> None:
    conn.execute(
        """INSERT INTO raw.files(sha256,source,url,path,bytes,content_type,extracted_at)
        VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(sha256) DO NOTHING""",
        (
            file.sha256,
            file.source,
            file.url,
            str(file.path),
            file.size,
            file.content_type,
            file.extracted_at,
        ),
    )


def check(
    conn: Any,
    run_id: str | None,
    name: str,
    status: str,
    observed: float | None,
    threshold: str,
    details: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO raw.quality_checks(run_id,check_name,status,observed,threshold,details) VALUES(%s,%s,%s,%s,%s,%s)",
        (run_id, name, status, observed, threshold, Jsonb(details or {})),
    )


def reference_data(conn: Any, year: int, refresh: bool) -> set[int]:
    zones = download(
        "TLC zones",
        "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
        "csv",
        refresh,
    )
    weather = download(
        "NOAA LaGuardia GSOD",
        f"https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/72503014732.csv",
        "csv",
        refresh,
    )
    for file in [zones, weather]:
        register_file(conn, file)
    with zones.path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"LocationID", "Borough", "Zone", "service_zone"}.issubset(reader.fieldnames or []):
            raise ValueError("Zone lookup schema drift")
        records = list(reader)
    ids = {int(row["LocationID"]) for row in records}
    if len(ids) != len(records):
        raise ValueError("Duplicate zone keys")
    for row in records:
        conn.execute(
            """INSERT INTO raw.zones VALUES(%s,%s,%s,%s,%s) ON CONFLICT(location_id)
            DO UPDATE SET borough=excluded.borough,zone=excluded.zone,service_zone=excluded.service_zone,source_hash=excluded.source_hash""",
            (
                int(row["LocationID"]),
                row["Borough"],
                row["Zone"],
                row["service_zone"],
                zones.sha256,
            ),
        )
    with weather.path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"STATION", "DATE", "TEMP", "PRCP"}.issubset(reader.fieldnames or []):
            raise ValueError("Weather schema drift")
        seen = set()
        for row in reader:
            if row["DATE"] in seen:
                raise ValueError("Duplicate weather reporting date")
            seen.add(row["DATE"])
            temp, precip = float(row["TEMP"]), float(row["PRCP"])
            conn.execute(
                """INSERT INTO raw.weather(weather_date,station,temp_c,precipitation_mm,source_hash)
                VALUES(%s,%s,%s,%s,%s) ON CONFLICT(weather_date) DO UPDATE SET
                temp_c=excluded.temp_c,precipitation_mm=excluded.precipitation_mm,source_hash=excluded.source_hash""",
                (
                    row["DATE"],
                    row["STATION"],
                    None if temp >= 9999 else (temp - 32) * 5 / 9,
                    None if precip >= 99 else precip * 25.4,
                    weather.sha256,
                ),
            )
    return ids


def ingest(
    month: str, limit: int = 100_000, refresh: bool = False, fail_after: int | None = None
) -> dict[str, Any]:
    partition = month_date(month)
    if limit < 0 or limit > 10_000_000:
        raise ValueError("Limit must be 0 (full partition) or 1–10,000,000")
    bootstrap()
    run_id, started = str(uuid.uuid4()), time.perf_counter()
    with connection() as conn:
        conn.execute(
            "INSERT INTO raw.ingestion_runs(id,partition_month,status,sample_limit) VALUES(%s,%s,'running',%s)",
            (run_id, partition, limit),
        )
    try:
        file = download(
            "TLC yellow trips",
            f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet",
            "parquet",
            refresh,
        )
        with connection() as file_conn:
            register_file(file_conn, file)
            file_conn.execute(
                "UPDATE raw.ingestion_runs SET source_hash=%s WHERE id=%s", (file.sha256, run_id)
            )
        duck = duckdb.connect()
        try:
            duck.execute("SET threads=2")
            duck.read_parquet(str(file.path)).create_view("input")
            columns = {row[0] for row in duck.execute("DESCRIBE input").fetchall()}
            extras = check_trip_schema(columns)
            check_trip_types({row[0]: row[1] for row in duck.execute("DESCRIBE input").fetchall()})
            count_row = duck.execute("SELECT count(*) FROM input").fetchone()
            assert count_row is not None
            source_rows = count_row[0]
            if source_rows == 0:
                raise ValueError("Source partition is empty")
            # Full-payload fingerprint is deterministic with pinned DuckDB; identical rows have no stable trip ID.
            sql = """SELECT md5(to_json(t)) AS trip_id, tpep_pickup_datetime AS pickup_at,
                tpep_dropoff_datetime AS dropoff_at, PULocationID AS pickup_zone,
                DOLocationID AS dropoff_zone, VendorID AS vendor_id, passenger_count,
                trip_distance AS distance_miles, fare_amount AS fare_usd, total_amount AS total_usd,
                payment_type FROM input t ORDER BY trip_id"""
            if limit:
                sql += f" LIMIT {int(limit)}"
            selected = duck.execute(sql)
            names = [item[0] for item in selected.description]
            accepted = rejected = duplicates = count = 0
            seen: set[str] = set()
            with connection() as conn:
                # Lock is per partition; readers retain the previous committed partition until commit.
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("atlasiq:" + month,))
                register_file(conn, file)
                zones = reference_data(conn, partition.year, refresh)
                previous = conn.execute(
                    "SELECT accepted_rows FROM raw.partitions WHERE month=%s", (partition,)
                ).fetchone()
                conn.execute("DELETE FROM raw.trips WHERE partition_month=%s", (partition,))
                with conn.cursor().copy(
                    f"COPY raw.trips ({','.join(TRIP_COLUMNS)}) FROM STDIN"
                ) as writer:
                    quarantine = []
                    while rows := selected.fetchmany(5000):
                        for values in rows:
                            row = dict(zip(names, values, strict=True))
                            count += 1
                            reason = validate_trip(row, month, zones)
                            if reason:
                                rejected += 1
                                quarantine.append(
                                    (
                                        run_id,
                                        row["trip_id"],
                                        reason,
                                        Jsonb(json.loads(json.dumps(row, default=str))),
                                    )
                                )
                            elif row["trip_id"] in seen:
                                duplicates += 1
                            else:
                                seen.add(row["trip_id"])
                                accepted += 1
                                writer.write_row(
                                    [partition]
                                    + [row[key] for key in names]
                                    + [file.sha256, run_id]
                                )
                            if fail_after is not None and count >= fail_after:
                                raise RuntimeError("Injected partial-load failure")
                if quarantine:
                    with conn.cursor() as cursor:
                        cursor.executemany(
                            "INSERT INTO raw.quarantine VALUES(%s,%s,%s,%s)", quarantine
                        )
                if accepted == 0:
                    raise ValueError("No accepted records; refusing to replace the partition")
                reject_rate = rejected / count
                if reject_rate > 0.10:
                    raise ValueError(f"Rejected fraction {reject_rate:.2%} exceeds 10% gate")
                conn.execute(
                    """INSERT INTO raw.partitions(month,run_id,source_hash,sample_limit,source_rows,accepted_rows)
                    VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(month) DO UPDATE SET run_id=excluded.run_id,
                    source_hash=excluded.source_hash,sample_limit=excluded.sample_limit,source_rows=excluded.source_rows,
                    accepted_rows=excluded.accepted_rows,loaded_at=now()""",
                    (partition, run_id, file.sha256, limit, source_rows, accepted),
                )
                check(
                    conn,
                    run_id,
                    "required_schema",
                    "pass",
                    len(columns),
                    "all required columns present",
                    {"additional_columns": extras},
                )
                check(
                    conn,
                    run_id,
                    "rejection_rate",
                    "pass" if reject_rate < 0.02 else "warning",
                    reject_rate,
                    "fail >10%; warn >=2%",
                )
                check(
                    conn,
                    run_id,
                    "duplicate_rate",
                    "pass" if duplicates / count < 0.01 else "warning",
                    duplicates / count,
                    "warn >=1%; exact-row dedup",
                )
                check(
                    conn,
                    run_id,
                    "row_count_change",
                    "warning"
                    if previous
                    and abs(accepted - previous["accepted_rows"]) / previous["accepted_rows"] > 0.25
                    else "pass",
                    accepted,
                    "warn >25% vs prior accepted partition; sampling changes require review",
                )
                check(
                    conn,
                    run_id,
                    "sample_coverage",
                    "warning" if limit else "pass",
                    accepted / source_rows,
                    "sample results are never expanded to population totals",
                )
                conn.execute(
                    """UPDATE raw.ingestion_runs SET status='loaded',finished_at=now(),source_hash=%s,
                    source_rows=%s,selected_rows=%s,accepted_rows=%s,rejected_rows=%s,duplicate_rows=%s,
                    elapsed_seconds=%s WHERE id=%s""",
                    (
                        file.sha256,
                        source_rows,
                        count,
                        accepted,
                        rejected,
                        duplicates,
                        time.perf_counter() - started,
                        run_id,
                    ),
                )
        finally:
            duck.close()
        report = dict(
            run_id=run_id,
            month=month,
            source_rows=source_rows,
            selected=count,
            accepted=accepted,
            rejected=rejected,
            duplicates=duplicates,
            seconds=round(time.perf_counter() - started, 3),
        )
        logger.info(json.dumps({"event": "partition_loaded", **report}))
        return report
    except Exception as exc:
        with connection() as conn:
            conn.execute(
                "UPDATE raw.ingestion_runs SET status='failed',error=%s,finished_at=now(),elapsed_seconds=%s WHERE id=%s",
                (str(exc)[:2000], time.perf_counter() - started, run_id),
            )
            check(
                conn,
                run_id,
                "ingestion_failure",
                "fail",
                None,
                "must complete atomically",
                {"error": str(exc)[:500]},
            )
        logger.exception(
            json.dumps({"event": "partition_failed", "run_id": run_id, "month": month})
        )
        raise
