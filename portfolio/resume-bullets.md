# Verifiable project bullets

Independent project; not employment. Run-specific measurements are conditional on the recorded local environment. Do not substitute these numbers for production-scale or causal claims.

## Data Engineering

- Built a monthly TLC/NOAA batch ingestion platform that scanned 3,475,226 real trip records and materialized 95,783 accepted rows from a deterministic 100,000-record sample.
- Implemented immutable SHA-256 landing, schema/domain validation, 4,217 quarantined sample rows, transaction advisory locks and atomic monthly partition replacement.
- Executed a five-task Airflow DAG test with real source data and verified idempotent replay without increasing the active trip count.
- Tested retryable/permanent HTTP failures, corrupt files, schema drift and partial-load rollback using a separate disposable PostgreSQL warehouse.

## Analytics Engineering

- Built 15 dbt models spanning staging, intermediate and dimensional marts, including an incremental trip fact and date/hour/zone/vendor/weather dimensions.
- Implemented changed-partition reloads that remove revised/deleted source rows rather than preserving stale append-only facts.
- Added unique/not-null/relationship, join-fanout, duration, partition-count and daily reconciliation tests with documented grains and missing-value semantics.
- Enforced a publication gate so metric endpoints do not serve newly loaded partitions before transformation and quality validation complete.

## Data Analytics

- Authored and executed 12 analytical SQL studies covering zone ranking, hourly/weekday demand, fare percentiles, weather-day associations and refresh reliability.
- Produced an insights report and chart from real queried results; identified Midtown Center as the highest-count pickup zone in the accepted sample with 4,676 observed trips.
- Defined an exploratory prior-same-weekday median/MAD method with minimum-history, scale and volume safeguards and documented short-history limitations.
- Documented deterministic sampling, fare/refund exclusions, daily station weather proxies and non-causal interpretations to avoid misleading conclusions.

## Software Engineering

- Built a typed FastAPI analytics service with bounded date/zone/pagination filters, parameterized PostgreSQL queries and helpful readiness/error responses.
- Implemented a strict TypeScript dashboard with seven views, real-data charts, zone comparisons, filter/drilldown interactions and error/retry states.
- Passed 28 Python tests covering source contracts, API behavior, data transformation, revision handling and recovery; see final verification for additional dbt/browser evidence.
- Containerized the API and isolated Airflow application environment and prepared CI for formatting, types, tests, frontend build and DAG parsing.
