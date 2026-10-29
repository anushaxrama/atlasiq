import csv
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import holidays

from .config import ROOT
from .db import connection
from .ingest import check


def seed_calendar() -> None:
    path = ROOT / "warehouse/seeds/federal_holidays.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["holiday_date", "holiday_name"])
        for day, name in sorted(holidays.US(years=range(2000, 2101), observed=True).items()):
            writer.writerow([day.isoformat(), name])


def dbt(command: str = "build") -> None:
    from .config import DATABASE_URL

    parsed = urlparse(DATABASE_URL)
    env = dict(
        os.environ,
        DBT_HOST=parsed.hostname or "127.0.0.1",
        DBT_PORT=str(parsed.port or 5432),
        DBT_USER=parsed.username or "atlasiq",
        DBT_PASSWORD=parsed.password or "",
        DBT_DATABASE=parsed.path.lstrip("/"),
        DBT_SEND_ANONYMOUS_USAGE_STATS="false",
    )
    executable = str(Path(sys.executable).parent / "dbt")
    if command in {"build", "seed"}:
        seed_calendar()
    if command == "build":
        subprocess.run(
            [
                executable,
                "seed",
                "--project-dir",
                str(ROOT / "warehouse"),
                "--profiles-dir",
                str(ROOT / "warehouse"),
            ],
            env=env,
            check=True,
        )
    subprocess.run(
        [
            executable,
            *command.split(),
            "--project-dir",
            str(ROOT / "warehouse"),
            "--profiles-dir",
            str(ROOT / "warehouse"),
        ],
        env=env,
        check=True,
    )


def validate() -> dict[str, Any]:
    tests = [
        (
            "fact_raw_reconciliation",
            "select abs((select count(*) from raw.trips)-(select count(*) from marts.fct_trips)) as value",
            0,
        ),
        (
            "weather_missing_fraction",
            "select coalesce(avg((weather_key is null)::integer),0) as value from marts.fct_trips",
            0.05,
        ),
        (
            "passenger_null_fraction",
            "select coalesce(avg((passenger_count is null)::integer),0) as value from raw.trips",
            0.20,
        ),
        (
            "unknown_zone_fraction",
            "select coalesce(avg((pickup_zone in (264,265))::integer),0) as value from raw.trips",
            0.10,
        ),
        (
            "refresh_age_hours",
            "select extract(epoch from now()-max(loaded_at))/3600 as value from raw.partitions",
            168,
        ),
    ]
    results = []
    with connection() as conn:
        latest = conn.execute(
            "select id from raw.ingestion_runs where status in ('loaded','published') order by started_at desc limit 1"
        ).fetchone()
        for name, sql, threshold in tests:
            result = conn.execute(sql).fetchone()
            assert result is not None
            value = result["value"]
            status = (
                "pass"
                if value is not None and float(value) <= threshold
                else "fail"
                if name == "fact_raw_reconciliation"
                else "warning"
            )
            check(
                conn,
                latest["id"] if latest else None,
                name,
                status,
                float(value) if value is not None else None,
                f"<= {threshold}",
            )
            results.append(
                dict(
                    check=name,
                    status=status,
                    value=float(value) if value is not None else None,
                    threshold=threshold,
                )
            )
    if any(item["status"] == "fail" for item in results):
        raise ValueError(json.dumps(results))
    return {
        "status": "warning" if any(item["status"] == "warning" for item in results) else "pass",
        "checks": results,
    }


def publish() -> None:
    validate()
    with connection() as conn:
        conn.execute(
            "UPDATE raw.ingestion_runs SET status='published',published_at=now() WHERE id IN (SELECT run_id FROM raw.partitions)"
        )


def months(start: str, end: str) -> list[str]:
    from .sources import month_date

    a, b = month_date(start), month_date(end)
    if a > b:
        raise ValueError("Backfill start must not follow end")
    result = []
    while a <= b:
        result.append(a.strftime("%Y-%m"))
        a = date(a.year + (a.month == 12), a.month % 12 + 1, 1)
    return result
