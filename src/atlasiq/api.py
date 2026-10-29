"""Bounded, parameterized, read-only analytics API over dbt marts."""

from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import query

STATIC = Path(__file__).parent / "static"
app = FastAPI(
    title="AtlasIQ Analytics API",
    version="0.1.0",
    description="Observed sampled NYC yellow-taxi trips, batch warehouse quality and NOAA weather associations. Fares are not profit; associations are not causation.",
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class Summary(BaseModel):
    observed_trips: int
    average_distance_miles: float | None
    average_duration_minutes: float | None
    average_fare_usd: float | None
    observed_fare_usd: float | None
    median_fare_usd: float | None
    p90_fare_usd: float | None


class Trend(BaseModel):
    date: date
    observed_trips: int
    average_fare_usd: float | None


class Hour(BaseModel):
    hour: int
    observed_trips: int


class Zone(BaseModel):
    zone_id: int
    zone_name: str
    borough: str
    observed_trips: int
    average_fare_usd: float | None
    average_distance_miles: float | None
    average_duration_minutes: float | None


class Weather(BaseModel):
    date: date
    temp_c: float | None
    precipitation_mm: float | None
    observed_trips: int
    average_duration_minutes: float | None


class Anomaly(BaseModel):
    date: date
    zone_id: int
    zone_name: str
    observed_trips: int
    median_trips: float | None
    robust_score: float | None
    n: int


class Quality(BaseModel):
    check_name: str
    status: str
    observed: float | None
    threshold: str
    checked_at: datetime
    details: dict[str, Any]


class Run(BaseModel):
    id: str
    partition_month: date
    status: str
    started_at: datetime
    finished_at: datetime | None
    accepted_rows: int | None
    rejected_rows: int | None
    selected_rows: int | None
    source_rows: int | None
    elapsed_seconds: float | None
    error: str | None


@app.exception_handler(psycopg.Error)
async def database_error(request: Any, exc: psycopg.Error) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Warehouse unavailable or not modeled. Run bootstrap, ingest and transform; see the operational runbook."
        },
    )


@app.middleware("http")
async def headers(request: Any, call_next: Any) -> Any:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = (
        "no-store" if request.url.path.startswith("/api") else "no-cache"
    )
    return response


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    query("select 1")
    return {"status": "ok", "database": "reachable"}


@app.get("/ready")
def ready() -> dict[str, str]:
    ensure_published()
    rows = query("select count(*) as n from marts.fct_trips")
    if rows[0]["n"] == 0:
        raise HTTPException(503, "Warehouse empty")
    return {"status": "ready"}


@app.get("/api/meta")
def metadata() -> dict[str, Any]:
    ensure_published()
    return {
        "coverage": query(
            "select min(pickup_date) as start,max(pickup_date) as end,count(*) as observed_trips from marts.fct_trips"
        )[0],
        "partitions": query(
            "select month,source_rows,accepted_rows,sample_limit,loaded_at from raw.partitions order by month"
        ),
        "zone_options": query(
            "select zone_id,zone_name,borough from marts.dim_zone order by zone_name"
        ),
        "mode": "deterministic sample; never expanded to population totals",
        "weather": "NOAA LaGuardia daily UTC reporting-day proxy; not zone-specific weather",
    }


def ensure_published() -> None:
    state = query("""select count(*) as total, count(*) filter(where r.status='published') as published
        from raw.partitions p join raw.ingestion_runs r on r.id=p.run_id""")[0]
    if state["total"] == 0 or state["total"] != state["published"]:
        raise HTTPException(
            503,
            "Warehouse refresh is not published yet. Quality gates must pass before analytics are served.",
        )


def parameters(start: date, end: date, zone: int | None) -> dict[str, Any]:
    if end < start or (end - start).days > 366:
        raise HTTPException(422, "Date range must be ordered and at most 367 calendar days")
    ensure_published()
    return {"start": start, "end": end, "zone": zone}


FILTER = "f.pickup_date between %(start)s and %(end)s and (%(zone)s::integer is null or f.pickup_zone=%(zone)s)"


@app.get("/api/summary", response_model=Summary)
def summary(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
) -> dict[str, Any]:
    return query(
        """select count(*) as observed_trips,avg(distance_miles) as average_distance_miles,
    avg(duration_minutes) as average_duration_minutes,avg(fare_usd) as average_fare_usd,
    sum(fare_usd) as observed_fare_usd,percentile_cont(.5) within group(order by fare_usd) as median_fare_usd,
    percentile_cont(.9) within group(order by fare_usd) as p90_fare_usd from marts.fct_trips f where """
        + FILTER,
        parameters(start, end, zone),
    )[0]


@app.get("/api/trends", response_model=list[Trend])
def trends(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
) -> list[dict[str, Any]]:
    return query(
        "select pickup_date as date,count(*) as observed_trips,avg(fare_usd) as average_fare_usd from marts.fct_trips f where "
        + FILTER
        + " group by 1 order by 1",
        parameters(start, end, zone),
    )


@app.get("/api/hourly", response_model=list[Hour])
def hourly(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
) -> list[dict[str, Any]]:
    return query(
        "select pickup_hour as hour,count(*) as observed_trips from marts.fct_trips f where "
        + FILTER
        + " group by 1 order by 1",
        parameters(start, end, zone),
    )


@app.get("/api/zones", response_model=list[Zone])
def zones(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
    limit: int = Query(25, ge=1, le=265),
    offset: int = Query(0, ge=0, le=10000),
) -> list[dict[str, Any]]:
    params = {**parameters(start, end, zone), "limit": limit, "offset": offset}
    return query(
        """select z.zone_id,z.zone_name,z.borough,count(*) as observed_trips,
    avg(f.fare_usd) as average_fare_usd,avg(distance_miles) as average_distance_miles,
    avg(duration_minutes) as average_duration_minutes from marts.fct_trips f
    join marts.dim_zone z on f.pickup_zone=z.zone_id where """
        + FILTER
        + " group by 1,2,3 order by observed_trips desc,z.zone_id limit %(limit)s offset %(offset)s",
        params,
    )


@app.get("/api/weather", response_model=list[Weather])
def weather(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
) -> list[dict[str, Any]]:
    return query(
        """select f.weather_date as date,w.temp_c,w.precipitation_mm,count(*) as observed_trips,
    avg(f.duration_minutes) as average_duration_minutes from marts.fct_trips f
    left join marts.dim_weather w on w.weather_key=f.weather_key where """
        + FILTER
        + " group by 1,2,3 order by 1",
        parameters(start, end, zone),
    )


@app.get("/api/anomalies", response_model=list[Anomaly])
def anomalies(
    start: date = date(2025, 1, 1),
    end: date = date(2025, 1, 31),
    zone: int | None = Query(None, ge=1, le=265),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
) -> list[dict[str, Any]]:
    return query(
        """select date,zone_id,zone_name,observed_trips,median_trips,robust_score,n from marts.mart_demand_anomalies
    where is_unusual and date between %(start)s and %(end)s and (%(zone)s::integer is null or zone_id=%(zone)s)
    order by abs(robust_score) desc,date desc limit %(limit)s offset %(offset)s""",
        {**parameters(start, end, zone), "limit": limit, "offset": offset},
    )


@app.get("/api/quality", response_model=list[Quality])
def quality(
    limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)
) -> list[dict[str, Any]]:
    return query(
        "select check_name,status,observed,threshold,checked_at,details from raw.quality_checks order by checked_at desc,id desc limit %(limit)s offset %(offset)s",
        {"limit": limit, "offset": offset},
    )


@app.get("/api/runs", response_model=list[Run])
def runs(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)
) -> list[dict[str, Any]]:
    return query(
        """select id::text,partition_month,status,started_at,finished_at,accepted_rows,rejected_rows,
    selected_rows,source_rows,elapsed_seconds,error from raw.ingestion_runs order by started_at desc limit %(limit)s offset %(offset)s""",
        {"limit": limit, "offset": offset},
    )
