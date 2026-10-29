# SQL analyses

These twelve queries answer specific questions about the accepted taxi sample. They read the modeled warehouse rather than the original Parquet files. Query results therefore reflect the ingestion rules, loaded months, and sample limit used for each partition.

## Run the report

With the warehouse loaded and the native development environment installed, run this from the repository root:

```sh
uv run atlasiq insights
```

The report generator executes every numbered SQL file and writes:

- [Query outputs and timings](../docs/evidence/analyses.json).
- [Written findings](../docs/INSIGHTS.md) and a demand chart.
- [Warehouse and run metadata](../docs/evidence/verification.json).
- [An EXPLAIN ANALYZE query plan](../docs/evidence/query-plan.json) for the documented date/zone lookup.

Individual files can also be run against the application database with a PostgreSQL client. They contain no application-supplied SQL fragments.

## Queries

| File | Question and calculation |
| --- | --- |
| [01_zone_ranking.sql](01_zone_ranking.sql) | Which pickup zones have the most accepted trips? Groups counts, joins official zone names, and applies dense ranking. |
| [02_weekday_hour.sql](02_weekday_hour.sql) | How does the sample vary by weekday and pickup hour? Uses the local calendar and accounts for covered dates. |
| [03_rolling_demand.sql](03_rolling_demand.sql) | How does daily zone demand change over a seven-day calendar window? Includes modeled zero-count dates. |
| [04_fare_distribution.sql](04_fare_distribution.sql) | How do fare distributions differ by borough? Calculates median, p90, and p99 with ordered-set percentiles. |
| [05_trip_efficiency.sql](05_trip_efficiency.sql) | How do distance and duration measures differ between zones with enough observed trips? Reports per-trip means rather than fleet-wide speeds. |
| [06_weather_association.sql](06_weather_association.sql) | How do observed trips differ between wet and dry reporting days? Uses matched daily station observations. |
| [07_holiday_comparison.sql](07_holiday_comparison.sql) | How do observed day averages differ around federal holidays? Uses the date dimension's federal observed calendar. |
| [08_week_over_week.sql](08_week_over_week.sql) | How does a zone/date compare with the same day seven days earlier? Joins exact calendar dates and leaves percentage change undefined for a zero denominator. |
| [09_unusual_demand.sql](09_unusual_demand.sql) | Which observations differ from their prior same-weekday baseline? Uses the documented median/MAD method. |
| [10_zone_flow.sql](10_zone_flow.sql) | Which pickup/dropoff pairs appear most often? Joins the zone dimension in both roles and calculates each pair's share. |
| [11_provider_mix.sql](11_provider_mix.sql) | How does the distribution of source provider codes vary by day? Uses a partitioned window denominator. |
| [12_refresh_and_rejections.sql](12_refresh_and_rejections.sql) | Do source, selected, accepted, rejected, and modeled counts reconcile? Also reports measured load duration. |

## Interpretation

The recorded report covers January through March 2025 with a 100,000-record selection per month. Because each month has the same cap, differences in accepted sample counts do not estimate changes in total NYC demand. Refund exclusions, invalid-record rejection, deterministic selection, and coverage gaps can affect every comparison.

Yellow taxi trips represent one service type. Base fares do not measure company revenue or profit. Daily LaGuardia weather is a city-level proxy, and UTC weather days can be partial at the edges of a local-date filter. Weather and holiday comparisons describe associations, not causal effects. Three months do not establish annual seasonality.

The retained query timings include local connection overhead. They are measurements of these executions, not production latency guarantees or evidence of a performance improvement.
