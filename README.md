# AtlasIQ — Urban Mobility & Economic Activity Intelligence

Project 02: an independent batch data platform for a new engineering portfolio. Official monthly NYC TLC Yellow taxi Parquet files, zone lookup data, NOAA station weather and a federal calendar flow through immutable landing, validated PostgreSQL loads, dbt star-schema models, typed analytics APIs and a responsive TypeScript dashboard.

AtlasIQ is **in development**, with a verified local vertical slice and container execution. It is not affiliated with NYC/TLC/NOAA, does not measure all mobility or the city economy, and has not been publicly deployed. No SignalFlow code or streaming infrastructure is used.

![AtlasIQ mobility dashboard](portfolio/screenshots/overview.png)

The dashboard includes daily/cumulative demand charts, keyboard point inspection, date shortcuts, filtered CSV exports, zone comparisons, and inspectable quality checks. All counts remain explicitly labeled as observations from the accepted sample.

## Quickstart

Requirements: Docker Compose; Python 3.12+ with uv; Node 24/pnpm 11.25 for frontend development. The committed compiled dashboard assets also work in Docker without a local Node install.

```sh
uv sync --frozen --extra dev
pnpm install --frozen-lockfile
pnpm build
docker compose up -d postgres
uv run atlasiq demo --month 2025-01 --limit 100000
uv run atlasiq serve --port 8020
```

Open **http://127.0.0.1:8020**; OpenAPI docs: **http://127.0.0.1:8020/docs**. PostgreSQL is bound locally on 5544. The bounded demo downloads the real 59 MB official Parquet file and selects a deterministic 100,000-record fingerprint sample. No raw files are committed. Default demonstration credentials are local only; replace them before any hosted deployment.

Alternatively, use containers for the application too:

```sh
docker compose up -d postgres
docker compose build api
docker compose run --rm api atlasiq demo --month 2025-01 --limit 100000
docker compose up -d api
```

A new/empty warehouse intentionally returns readiness/analytics 503 until ingest, transform, quality and publish complete. `/health` checks database connectivity; `/ready` checks publication readiness. Do not run the native server and Compose API on the same port simultaneously.

## What is implemented

- Bounded HTTP extraction with retries, jitter/Retry-After, content checks, immutable SHA-256 files and corrupt-cache detection.
- Month validation, audited runs, schema contracts, exact-payload deduplication, reasoned quarantine and atomic partition replacement.
- `raw`, `staging`, `intermediate` and `marts` schemas; incremental changed-partition trip facts; date/time/zone/vendor/weather dimensions.
- Daily zone, hourly demand, efficiency/fare percentiles, weather comparison, exploratory median/MAD anomalies and refresh-health marts.
- Read-only typed FastAPI endpoints with parameterized SQL, bounded date/zone/pagination inputs and publication gating.
- Seven real-data dashboard views: Overview, Demand Explorer, Zone Comparison, Weather & Demand, Data Quality, Pipeline Runs and Methodology.
- Five-task Airflow monthly DAG with retries/timeouts, explicit partition backfills, no import-time source calls and actionable log alerts.
- 12 substantive SQL analyses and an insights report generated from executed results, including measured query plans.
- Unit/integration/contracts/API/recovery/dbt/DAG and desktop/mobile end-to-end validation; CI configuration.

The lean strict TypeScript/SVG frontend is deliberate: it consumes the real API while prioritizing warehouse engineering over frontend framework infrastructure. No runtime frontend dependencies, authentication service, database-as-a-service or paid cloud account are required locally.

## Commands

```sh
uv run atlasiq bootstrap
uv run atlasiq ingest --month 2025-01 --limit 100000
uv run atlasiq ingest --month 2025-01 --limit 100000 --refresh
uv run atlasiq backfill --start 2025-01 --end 2025-02 --limit 100000
uv run atlasiq transform
uv run atlasiq validate
uv run atlasiq publish
uv run atlasiq insights
```

`--limit 0` loads a full source month; this increases processing and memory requirements and has not been benchmarked here. The default is a development sample, not an unbiased population estimate. Cache reuse is checksummed. `--refresh` explicitly fetches revised upstream bytes; unchanged files preserve identity. A failed source request, corrupted file, schema gate or partial load leaves the prior active partition intact. A successful raw replacement closes the serving gate until transforms and checks publish it.

## Tests and evidence

```sh
uv run ruff check src tests orchestration
uv run ruff format --check src tests orchestration
uv run mypy src
uv run pytest -q
pnpm typecheck
pnpm build
PLAYWRIGHT_USE_CHROME=1 pnpm test:e2e
```

Database tests are skipped unless `TEST_ATLAS_DATABASE_URL` points explicitly to a disposable database named `atlasiq_test`, distinct from the application DB. Create that database with your local administrative credentials, then:

```sh
TEST_ATLAS_DATABASE_URL=postgresql://atlasiq:atlasiq_local@127.0.0.1:5544/atlasiq_test uv run pytest -q
```

Integration tests only use labeled synthetic fixtures and do not require massive downloads or source network access. Browser tests use the running real-data application; Playwright's installed Chrome option avoids a separate browser download. Alternatively install Chromium with `pnpm exec playwright install chromium` and omit that environment variable. Mobile tests use browser viewport/touch emulation, not real-device Safari.

See [verification](docs/VERIFICATION.md), [actual insights](docs/INSIGHTS.md), [query outputs](docs/evidence/analyses.json), [run evidence](docs/evidence/verification.json), and [source contracts](docs/SOURCES.md). A committed CI workflow is not a verified remote CI run.

## Orchestration

```sh
docker compose --profile orchestration up --build -d airflow
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags trigger atlasiq_monthly --conf '{"month":"2025-01","limit":100000}'
```

Airflow UI: http://127.0.0.1:8082. Its standalone initialization writes the initial local admin password inside the Airflow container; inspect it locally instead of committing it. The DAG starts paused. The monthly schedule targets a source month about two months behind the interval end. Confirm source publication before unpausing; failed/missing future partitions fail explicitly. A successful full `airflow dags test` was executed; this does not claim a production scheduler history.

## Technical documentation

- [Architecture and lineage](docs/ARCHITECTURE.md), [ER model](docs/ER.md), [data dictionary](docs/DATA_DICTIONARY.md), [ADRs](docs/ADRS.md).
- [Operations and recovery](docs/RUNBOOK.md), [troubleshooting and deployment](docs/DEPLOYMENT.md), [SQL analysis guide](analyses/README.md).
- [Copy-ready engineering case study](portfolio/case-study.md), [role positioning](portfolio/role-positioning.md), [resume bullets](portfolio/resume-bullets.md), [interview guide](portfolio/interview-guide.md), [portfolio entry](portfolio/portfolio-entry.json).

NYC TLC attribution and NYC source terms apply to the trip data; NOAA GSOD attribution/metadata apply to weather. Federal calendar rules are derived using pinned python-holidays and checked against the documented OPM scope. Original sources do not guarantee complete or perfectly accurate observations. Documentation explains sampling, refunds/exclusions, unknown zones, timestamp interpretation, daily weather proxies, and non-causal comparisons. No fabricated company affiliations, achievements, benchmarks or deployed URLs are included.

Configuration is read from process environment. To use a local `.env`, run commands with `uv run --env-file .env atlasiq ...`; Compose reads its own service environment. Do not commit real credentials. Measured index/query context is documented in [performance notes](docs/PERFORMANCE.md).
