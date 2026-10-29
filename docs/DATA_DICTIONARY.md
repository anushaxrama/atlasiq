# Data dictionary and contracts

| Relation | Grain/key | Important fields / units |
| --- | --- | --- |
| raw.files | SHA-256 source content | URL, source, extracted_at UTC, local path, bytes, content type |
| raw.ingestion_runs | Run UUID | Month, source/selected/accepted/rejected/duplicate counts, status, duration seconds, error |
| raw.partitions | Source month | Active run UUID, source hash, sample limit, source and accepted counts, loaded_at |
| raw.trips | Month + exact source-payload MD5 | NYC wall-clock pickup/dropoff, TLC zone keys, miles, observed fare/total USD, passenger count, source/run provenance |
| raw.zones | TLC LocationID | Official name, borough, service zone; current lookup |
| raw.weather | One station reporting date | LaGuardia station, mean temperature °C, precipitation mm; sentinel values null |
| raw.quarantine | Run + rejected record hash | Explicit reason and selected source fields; full original bytes remain in landing file |
| raw.quality_checks | Check ID | Run, observed value, threshold, status, details, checked_at |
| marts.fct_trips | Accepted month + fingerprint | Date/hour/zone/vendor/weather keys; derived duration minutes and per-trip mph |
| marts.dim_date | NYC pickup date key YYYYMMDD | Weekday, weekend, federal observed holiday; only loaded partition calendars |
| marts.dim_time | Hour 0–23 | Local time-of-day period |
| marts.dim_zone | Location ID | Same dimension plays pickup and dropoff roles |
| marts.dim_weather | UTC reporting date key | Daily station observations; one weather row per key |
| marts.dim_vendor | Source provider code | Yellow taxi type; no fabricated company mappings |
| marts.mart_daily_zone | Date × official pickup zone | Count, mean distance/duration, observed fare sum, rolling seven-calendar-day mean |
| marts.mart_hourly_demand | Pickup date × hour × zone | Counts and mean trip measures |
| marts.mart_trip_efficiency | Pickup zone | Observed counts, per-trip means, median/p90 fare |
| marts.mart_weather_demand | UTC reporting date | Matched weather and observed counts; filter-edge days can be partial |
| marts.mart_demand_anomalies | Local date × zone | Prior same-weekday median, MAD, history count, robust score, exploratory flag |
| marts.mart_refresh_health | Active source month | Reconciliation of accepted vs modeled rows and measured load runtime |

Sampling: order the pinned-DuckDB full-payload MD5 fingerprint and select the first k rows (default 100,000). This is deterministic and spreads selection over source records instead of taking the first chronological records. It is not asserted to be a formal unbiased probability sample. Do not extrapolate population totals or compare counts across differently sized samples without care. Exact duplicate rows share an identity; indistinguishable legitimate trips and theoretical MD5 collisions are limitations.

Exclusions: missing/out-of-month timestamps; nonpositive or >360 minute durations; negative/nonfinite/oversized amounts or distances; invalid passenger counts; unknown lookup IDs. Source refunds/negative adjustments are quarantined rather than included in positive-trip KPI definitions. These decisions bias the sample toward valid positive trips and are documented, not hidden cleaning.

Weather alignment: convert NYC pickup wall time to UTC, take that date and join the unique NOAA daily reporting date. Both temperature and precipitation stay null for missing sentinel values. No zone-specific weather, hourly precision, or causal weather effect is claimed.
