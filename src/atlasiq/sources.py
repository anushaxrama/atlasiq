"""Official HTTP downloads, immutable hash storage and explicit schema contracts."""

import hashlib
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .config import DATA

logger = logging.getLogger("atlasiq")
REQUIRED_TRIP_FIELDS = {
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
    "payment_type",
    "passenger_count",
}


@dataclass(frozen=True)
class LandedFile:
    source: str
    url: str
    path: Path
    sha256: str
    size: int
    content_type: str
    extracted_at: str


def month_date(month: str) -> date:
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", month):
        raise ValueError("Month must use YYYY-MM, between 2000 and 2099")
    return date.fromisoformat(month + "-01")


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(source: str, url: str, extension: str, refresh: bool = False) -> LandedFile:
    folder = DATA / "landing"
    folder.mkdir(parents=True, exist_ok=True)
    reference = folder / (hashlib.sha256(url.encode()).hexdigest() + ".json")
    if reference.exists() and not refresh:
        meta = json.loads(reference.read_text())
        path = folder / meta["filename"]
        if not path.is_file() or checksum(path) != meta["sha256"]:
            raise ValueError("Cached file checksum mismatch; investigate, then use --refresh")
        return LandedFile(
            source,
            url,
            path,
            meta["sha256"],
            path.stat().st_size,
            meta["content_type"],
            meta["extracted_at"],
        )
    temp = folder / (reference.stem + ".part")
    for attempt in range(4):
        try:
            with httpx.Client(
                timeout=httpx.Timeout(90, connect=15), follow_redirects=True
            ) as client:
                with client.stream(
                    "GET", url, headers={"User-Agent": "AtlasIQ/0.1 educational portfolio"}
                ) as response:
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise httpx.HTTPStatusError(
                            "Retryable source error", request=response.request, response=response
                        )
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if not any(
                        t in content_type for t in ["csv", "text/plain", "octet-stream", "parquet"]
                    ):
                        raise ValueError(f"Unexpected content type: {content_type}")
                    with temp.open("wb") as output:
                        size = 0
                        for block in response.iter_bytes(1024 * 1024):
                            size += len(block)
                            if size > 2_000_000_000:
                                raise ValueError("Source exceeds the 2 GB safety bound")
                            output.write(block)
            if temp.stat().st_size == 0:
                raise ValueError("Empty source response")
            digest = checksum(temp)
            path = folder / f"{digest}.{extension}"
            temp.replace(path)
            extracted_at = datetime.now(timezone.utc).isoformat()
            metadata = dict(
                filename=path.name,
                sha256=digest,
                content_type=content_type,
                extracted_at=extracted_at,
                url=url,
                source=source,
            )
            reference.with_suffix(".tmp").write_text(json.dumps(metadata, indent=2))
            reference.with_suffix(".tmp").replace(reference)
            logger.info(
                json.dumps(
                    {
                        "event": "source_landed",
                        "source": source,
                        "bytes": path.stat().st_size,
                        "sha256": digest,
                    }
                )
            )
            return LandedFile(
                source, url, path, digest, path.stat().st_size, content_type, extracted_at
            )
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            retryable = isinstance(exc, httpx.TransportError) or exc.response.status_code in {
                429,
                500,
                502,
                503,
                504,
            }
            if not retryable or attempt == 3:
                raise
            retry_after = (
                exc.response.headers.get("Retry-After", "")
                if isinstance(exc, httpx.HTTPStatusError)
                else ""
            )
            delay = (
                min(float(retry_after), 60)
                if retry_after.isdigit()
                else min(2**attempt + random.random(), 30)
            )
            time.sleep(delay)
        finally:
            temp.unlink(missing_ok=True)
    raise RuntimeError("Download attempts exhausted")


def check_trip_schema(columns: set[str]) -> list[str]:
    missing = REQUIRED_TRIP_FIELDS - columns
    if missing:
        raise ValueError(f"Schema drift: missing required columns {sorted(missing)}")
    return sorted(columns - REQUIRED_TRIP_FIELDS)


def validate_trip(row: dict[str, Any], month: str, zones: set[int]) -> str | None:
    import math

    start, end = row["pickup_at"], row["dropoff_at"]
    if start is None or end is None:
        return "missing_timestamp"
    if start.strftime("%Y-%m") != month:
        return "pickup_outside_partition"
    duration = (end - start).total_seconds() / 60
    if duration <= 0 or duration > 360:
        return "duration_outside_0_360_minutes"
    for field, maximum in [("distance_miles", 200), ("fare_usd", 1000), ("total_usd", 2000)]:
        value = row[field]
        if value is None or not math.isfinite(float(value)) or value < 0 or value > maximum:
            return f"invalid_{field}"
    if row["pickup_zone"] not in zones or row["dropoff_zone"] not in zones:
        return "unknown_zone"
    passengers = row["passenger_count"]
    if passengers is not None and (
        not math.isfinite(float(passengers)) or passengers < 0 or passengers > 9
    ):
        return "invalid_passenger_count"
    return None


def check_trip_types(schema: dict[str, str]) -> None:
    for name in ("tpep_pickup_datetime", "tpep_dropoff_datetime"):
        if not schema[name].startswith("TIMESTAMP"):
            raise ValueError(f"Schema drift: {name} must be a timestamp, got {schema[name]}")
    numeric = (
        "TINYINT",
        "SMALLINT",
        "INTEGER",
        "BIGINT",
        "HUGEINT",
        "DOUBLE",
        "FLOAT",
        "DECIMAL",
        "UTINYINT",
        "USMALLINT",
        "UINTEGER",
        "UBIGINT",
        "UHUGEINT",
    )
    for name in REQUIRED_TRIP_FIELDS - {"tpep_pickup_datetime", "tpep_dropoff_datetime"}:
        if not schema[name].startswith(numeric):
            raise ValueError(f"Schema drift: {name} must be numeric, got {schema[name]}")
