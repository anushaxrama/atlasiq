# Measured performance and query tuning

Environment: local macOS ARM64 host, Python 3.12, PostgreSQL 16 in Docker Desktop, DuckDB scan with two threads. January 2025 source file 59,158,238 bytes / 3,475,226 rows; 100,000 selected / 95,783 accepted. Exact local environment and run durations appear in `evidence/verification.json`. No full-month or production service benchmark is claimed.

The recorded filtered aggregation (pickup dates January 10–12, zone 237) used the **atlas_fact_date_zone index-only scan** with 381 qualifying rows, zero heap fetches and warm shared buffers. PostgreSQL reported planning **0.197 ms** and execution **0.067 ms** for this single query. This is one cache-dependent local plan, not endpoint latency or an improvement over an unmeasured baseline. Full EXPLAIN ANALYZE/BUFFERS JSON is retained.

The `(pickup_date,pickup_zone)` fact index supports date-bounded drilldowns; the weather-date index supports aligned reporting-date joins. Broad all-month aggregations may appropriately choose sequential scans. A future zone-leading index should only be added after measuring actual workloads and write/storage cost. API connections currently open per query; report timings include connection overhead.

| Analysis | Rows returned | Measured query + connection seconds |
|---|---:|---:|
| 01_zone_ranking | 20 | 0.039323 |
| 02_weekday_hour | 168 | 0.071380 |
| 03_rolling_demand | 93 | 0.014638 |
| 04_fare_distribution | 8 | 0.028916 |
| 05_trip_efficiency | 20 | 0.009100 |
| 06_weather_association | 2 | 0.005600 |
| 07_holiday_comparison | 2 | 0.008883 |
| 08_week_over_week | 30 | 0.007223 |
| 09_unusual_demand | 30 | 0.006686 |
| 10_zone_flow | 43 | 0.016845 |
| 11_provider_mix | 75 | 0.012074 |
| 12_refresh_and_rejections | 1 | 0.005692 |

Initial ingestion took 6.5076 seconds including extraction/reference work; an independent Airflow replay took 7.2139 seconds. Network, caches, host contention and sampling matter. No throughput improvement, sustained request capacity or SLA is inferred. Full loads retain an in-memory deduplication set; optional larger historical backfills need explicit resource sizing.
