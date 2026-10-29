# AtlasIQ

AtlasIQ is a batch data pipeline and analytics application for NYC Yellow taxi trips. It downloads the official monthly Parquet files, validates the records, loads PostgreSQL, builds a dbt warehouse, and serves the results through FastAPI and a TypeScript dashboard. Daily NOAA station observations and a federal holiday calendar provide context for the trip data.

The project focuses on what happens between downloading a file and trusting a chart: retaining source provenance, handling rejected records, replacing revised monthly partitions, checking model relationships, and keeping unpublished loads out of the serving API.

![AtlasIQ dashboard](portfolio/screenshots/overview.png)

[Build checks](https://github.com/anushaxrama/atlasiq/actions/workflows/ci.yml) | [Architecture](docs/ARCHITECTURE.md) | [Backfill results](docs/MULTI_MONTH_BACKFILL.md) | [Runbook](docs/RUNBOOK.md)

## What is included

- Monthly TLC ingestion with bounded retries, file checksums, source-schema validation, and a reproducible sample option.
- PostgreSQL storage for source metadata, accepted trips, rejected records, active partitions, quality checks, and run history.
- A dbt star schema with an incremental trip fact, dimensions, analytical marts, and 17 data tests.
- A five-task Airflow DAG for bootstrap, ingestion, transformation, validation, and publication.
- Typed, read-only FastAPI endpoints with parameterized SQL and bounded inputs.
- Seven dashboard views covering overview metrics, demand, zone comparisons, weather, quality checks, run history, and methodology.
- Daily and cumulative charts, keyboard point inspection, date shortcuts, and filtered CSV exports.
- Twelve SQL analyses with query outputs and an insights report generated from the warehouse.

The frontend uses strict TypeScript, SVG, and CSS without a runtime framework. The compiled assets are committed, so the Docker application can run without installing Node locally.

## Recorded dataset and backfill results

The verified local warehouse covers January 1 through March 31, 2025. Each monthly file is scanned, and a deterministic 100,000-record selection is validated before loading.

| Month | Source rows | Selected | Accepted | Rejected |
| --- | ---: | ---: | ---: | ---: |
| January 2025 | 3,475,226 | 100,000 | 95,783 | 4,217 |
| February 2025 | 3,577,543 | 100,000 | 94,764 | 5,236 |
| March 2025 | 4,145,257 | 100,000 | 94,352 | 5,648 |
| Total | 11,198,026 | 300,000 | 284,899 | 15,101 |

February was then replayed through ingestion, dbt, validation, and publication. All three raw and fact partitions retained identical counts and sorted trip-ID fingerprints. January and March kept their existing active run IDs; February received a new active run. Both combined builds passed all 17 dbt tests, and no accepted trip had an unmatched weather key.

The API reconciled to 284,899 accepted trips over 90 pickup dates. The [execution record](docs/evidence/multi-month-backfill.json) includes source URLs, file sizes, SHA-256 checksums, run IDs, before/after fingerprints, weather matching, and actual dbt results.

These are local execution results, not data bundled with the repository. A fresh clone starts without the source files or a populated database.

## Run with Docker

Install Docker Engine or Docker Desktop with Compose, then:

```sh
git clone https://github.com/anushaxrama/atlasiq.git
cd atlasiq
docker compose up -d postgres
docker compose build api
docker compose run --rm api atlasiq demo --month 2025-01 --limit 100000
docker compose up -d api
```

Open [http://127.0.0.1:8020](http://127.0.0.1:8020). API documentation is at [http://127.0.0.1:8020/docs](http://127.0.0.1:8020/docs).

The first demo downloads the real January source file, approximately 59 MB, plus reference data. It scans the source file and selects 100,000 records; it does not stop downloading after 100,000 records. Network access is required for ingestion. Subsequent runs can reuse checksummed cached files.

PostgreSQL is exposed locally on port 5544. The API uses port 8020, and the optional Airflow UI uses 8082. Database and landing-file volumes persist across normal container restarts. Compose credentials are for local development.

### Load the verified three-month range

After the January demo:

```sh
docker compose exec api atlasiq backfill --start 2025-02 --end 2025-03 --limit 100000
```

The range is inclusive. The command loads the requested partitions, runs dbt, validates the warehouse, and publishes the active partitions. To replay February:

```sh
docker compose exec api atlasiq demo --month 2025-02 --limit 100000
```

The [backfill guide](docs/MULTI_MONTH_BACKFILL.md) explains the verification procedure and what the retained fingerprints prove.

## Native development

Use Python 3.12, uv, and PostgreSQL. Frontend development uses Node 24 and pnpm 11.25. The project declares Python 3.12 and 3.13 support; the recorded development and CI checks use 3.12.

From the cloned repository:

```sh
uv sync --frozen --extra dev
pnpm install --frozen-lockfile
pnpm build
docker compose up -d postgres
uv run atlasiq demo --month 2025-01 --limit 100000
uv run atlasiq serve --port 8020
```

Do not run the native server and Compose API on port 8020 at the same time. Native execution defaults to the PostgreSQL instance on `127.0.0.1:5544` and stores landed files under `data/`. Compose uses its internal service address and a landing volume.

| Variable | Purpose |
| --- | --- |
| `ATLAS_DATABASE_URL` | PostgreSQL connection string; defaults to the local Compose database on port 5544 |
| `ATLAS_DATA_DIR` | Directory for landed source files; defaults to `data/` in native development |
| `DBT_SEND_ANONYMOUS_USAGE_STATS` | Set to `false` by the dbt runner and Compose environment |
| `TEST_ATLAS_DATABASE_URL` | Explicit connection to a separate disposable `atlasiq_test` database |

Configuration comes from process environment variables. For a native `.env` file, use `uv run --env-file .env atlasiq ...`. Real credentials and landed data should remain outside Git.

## Pipeline and warehouse

```text
TLC monthly Parquet + zone lookup + NOAA observations
    -> immutable landed files and checksums
    -> schema checks, deterministic selection, and row validation
    -> PostgreSQL raw tables and quarantine
    -> dbt staging, intermediate models, dimensions, and marts
    -> quality checks and publication
    -> FastAPI, dashboard, CSV exports, and SQL analyses
```

### Ingestion and source identity

Every landed file retains its URL, retrieval time, byte count, and SHA-256 checksum. HTTP extraction handles timeouts, rate limits, bounded retries, content checks, and corrupt cache entries.

TLC does not supply a stable trip ID in these files. AtlasIQ computes a full-payload MD5 fingerprint using the pinned DuckDB version. Exact duplicate source rows share an identity. Identical legitimate trips cannot be distinguished, and hash collisions remain a theoretical limitation.

The default sample selects the lowest 100,000 fingerprints in each source month. It is reproducible but is not treated as a formally unbiased probability sample. `--limit 0` loads the full partition and requires more memory and processing time; full-month performance has not been benchmarked.

Validation checks timestamp boundaries, duration, numeric values, passenger counts, and lookup keys. Rejected records retain a reason and source provenance. Refunds and negative fare adjustments are excluded from the positive-trip KPI sample, which affects the resulting distribution.

### Partition replacement and serving readiness

A PostgreSQL transaction and a partition advisory lock protect each raw monthly replacement. A failed request, invalid file, schema failure, or interrupted load leaves the previous active partition intact. When a raw replacement succeeds, its run becomes the partition's active source.

The incremental dbt fact replaces changed partitions by active run ID. Removed source rows are removed from the corresponding modeled partition; unchanged months are preserved.

A newly loaded partition is not immediately available to analytical clients. The API's serving gate stays closed until transformations, quality checks, and publication complete. `/health` checks database connectivity; `/ready` checks that active partitions are published. A new or unmodeled warehouse intentionally returns 503 for analytical requests. Run and quality endpoints remain available for diagnosis.

A range backfill commits one raw month at a time. If a later month fails, earlier successful loads remain durable. Correct the issue and retry the affected range.

### Model structure

| Schema or model | Purpose |
| --- | --- |
| `raw` | Files, runs, active partitions, accepted trips, zones, weather, quarantine, and quality results |
| `staging` | Source typing, trip duration, local date/hour, and weather-date derivation |
| `intermediate` | Shared daily zone calculations |
| `marts.fct_trips` | One accepted trip per source month and payload fingerprint |
| `marts.dim_date`, `dim_time` | Local pickup calendar and hour definitions |
| `marts.dim_zone` | Official TLC zone lookup, used for pickup and dropoff roles |
| `marts.dim_vendor`, `dim_weather` | Source provider codes and unique daily weather observations |
| Analytical marts | Demand by date/hour/zone, fares and efficiency, weather comparisons, anomalies, and refresh health |

See the [ER model](docs/ER.md) and [data dictionary](docs/DATA_DICTIONARY.md) for keys, grains, units, and field definitions.

## Analytical definitions

Daily and hourly demand use NYC pickup wall-clock time. Weather matching converts pickup time to UTC, takes that date, and joins one NOAA LaGuardia reporting-day observation. This prevents a date join from multiplying trips. Missing weather values remain null. One station's daily observations are a city-level proxy, not neighborhood or hourly weather.

Average fare is the observed base fare in USD. It is not total trip charges, driver income, company revenue, or profit. Durations and distances are calculated from accepted source records, so validation exclusions matter when comparing groups.

Demand flags compare a zone/date with prior same-weekday dates in a 56-day window. They require at least three prior dates and use a median/MAD baseline with a denominator floor. Short history, sample selection, and external events limit interpretation. The flags are prompts to investigate, not confirmed incidents.

Each month has the same sample cap, so differences in accepted monthly sample totals do not estimate city-wide demand growth. Three historical months do not establish annual seasonality. Weather comparisons are descriptive associations rather than causal findings.

## API and dashboard

Analytical endpoints accept ISO date parameters `start` and `end`, plus an optional TLC pickup `zone`. Date ranges are limited to 367 inclusive days. Zone and pagination inputs are bounded, and SQL statements have a timeout.

| Endpoint | Response |
| --- | --- |
| `/api/meta` | Loaded coverage, active partitions, zone options, and dataset definitions |
| `/api/summary` | Trip count, distance, duration, and fare statistics |
| `/api/trends` | Daily observed counts and mean fares |
| `/api/hourly` | Local pickup-hour counts |
| `/api/zones` | Zone-level measures and ranking |
| `/api/weather` | NOAA observations alongside matched trip measures |
| `/api/anomalies` | Exploratory same-weekday demand flags |
| `/api/quality` | Executed checks, statuses, thresholds, and observations |
| `/api/runs` | Ingestion outcomes, counts, partitions, and runtime |
| `/health`, `/ready` | Connectivity and publication readiness |
| `/docs` | Interactive endpoint documentation |

For example:

```sh
curl 'http://127.0.0.1:8020/api/summary?start=2025-01-01&end=2025-03-31&zone=161'
```

The dashboard's daily CSV export uses the applied date and zone filters. It exports aggregate daily observations, not original trip-level source files. The cumulative chart is the running sum of those observed daily counts.

## Commands

```sh
uv run atlasiq bootstrap
uv run atlasiq ingest --month 2025-02 --limit 100000
uv run atlasiq transform
uv run atlasiq validate
uv run atlasiq publish
uv run atlasiq insights
```

`demo` combines ingestion, transformation, validation, and publication for one month. `backfill` does that work for an inclusive month range. `ingest` alone stops after the raw load. Use `--refresh` with ingestion when deliberately fetching a revised upstream file rather than reusing cached bytes.

`insights` executes the analytical SQL and writes [query results](docs/evidence/analyses.json), [findings](docs/INSIGHTS.md), a demand chart, and a measured query plan. Run it in the native development checkout when updating these tracked documents.

## Airflow

```sh
docker compose --profile orchestration up --build -d airflow
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags trigger atlasiq_monthly --conf '{"month":"2025-02","limit":100000}'
```

The UI is at [http://127.0.0.1:8082](http://127.0.0.1:8082). Standalone initialization writes the initial local admin password inside the container. Keep those credentials local.

The `atlasiq_monthly` DAG starts paused and is scheduled for the 15th of each month at 06:00 UTC. It normally targets a source month about two months earlier; `dag_run.conf` can override the month and sample limit. The five tasks run in order: bootstrap, ingest, transform, validate, publish. Retries, exponential retry delay, and task/DAG timeouts are configured. The failure callback writes a structured log message; external notification delivery is not configured.

The complete five-task DAG was executed successfully with `airflow dags test`. That verifies task execution, not a sustained production scheduler history. Check upstream publication and NOAA coverage before scheduling later months.

## Tests and verification

Install development dependencies with `uv sync --frozen --extra dev`, then:

```sh
uv run ruff check src tests orchestration
uv run ruff format --check src tests orchestration
uv run mypy src
uv run pytest -q
pnpm format:check
pnpm typecheck
pnpm build
```

Database tests require a separate disposable database named `atlasiq_test`. They do not run against the application warehouse. To create one in the local Compose instance, run the following once if it does not already exist:

```sh
docker compose exec postgres createdb -U atlasiq atlasiq_test
TEST_ATLAS_DATABASE_URL=postgresql://atlasiq:atlasiq_local@127.0.0.1:5544/atlasiq_test uv run pytest -q
```

Without that environment variable, database-dependent tests are skipped. The integration fixtures are synthetic and isolated; source downloads are not required for the Python suite.

Browser tests need the running application with ingested data. With Chrome installed:

```sh
PLAYWRIGHT_USE_CHROME=1 pnpm test:e2e
```

Alternatively, run `pnpm exec playwright install chromium`, then `pnpm test:e2e`. The cross-month browser check requires at least two loaded partitions and is skipped for a one-month demo. Mobile checks use viewport/touch emulation in Chromium, not real-device Safari.

Recorded checks include 28 Python tests, 17 dbt tests, a complete five-task Airflow execution, and 12 desktop/mobile browser checks against the three-month warehouse. Browser checks cover all seven views, date and zone filters, cross-month totals, keyboard chart inspection, CSV reconciliation, comparisons, empty states, and outage recovery.

[GitHub Actions](https://github.com/anushaxrama/atlasiq/actions/workflows/ci.yml) runs Python linting, formatting, types, and tests with a separate PostgreSQL service; checks and builds the frontend; validates Compose; and builds the Airflow image to parse its DAG. The real-data browser journeys and historical backfill are separate recorded local checks. CI does not download and recreate the entire historical dataset on each push.

## Limits and follow-up work

This is a verified local application with a public source repository. It does not have a hosted application endpoint, production authentication, a multi-user operating history, or a full-scale throughput benchmark.

The sample and rejection rules limit analytical conclusions. TLC records can be incomplete or revised. NOAA's 2025 GSOD archive has a limited coverage horizon; newer backfills may need a documented successor adapter. The calendar covers US federal observed holidays, not every NYC closure or local event.

Operational work before a hosted deployment includes schema migrations, backups with tested restoration, access controls, external alert delivery, and load testing. Raw partition replacement is transactional, but dbt publishes several relations sequentially; serving-table version swaps would be a useful next step for uninterrupted analytical reads during a rebuild.

## Repository layout

```text
src/atlasiq/       Ingestion, source contracts, database, CLI, API, and compiled UI
frontend/         Strict TypeScript dashboard source
warehouse/        dbt models, tests, profiles, and calendar seed
orchestration/    Airflow DAG and image definition
analyses/         Twelve SQL analyses and their guide
tests/            Python tests and browser journeys
docs/             Architecture, operations, findings, and measured evidence
portfolio/        Case study, interview notes, and application screenshots
```

More detail: [design decisions](docs/ADRS.md), [operations and recovery](docs/RUNBOOK.md), [performance notes](docs/PERFORMANCE.md), [verification history](docs/VERIFICATION.md), and [engineering case study](portfolio/case-study.md).

## Sources and attribution

Trip files and zone names come from [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page). NYC source terms apply. Weather comes from [NOAA Global Summary of the Day](https://www.ncei.noaa.gov/products/land-based-station/global-summary-of-the-day), with its source metadata retained. Federal observed holidays use pinned `python-holidays` rules and the documented OPM scope.

AtlasIQ is an independent project, not affiliated with TLC or NOAA. The [source notes](docs/SOURCES.md) describe attribution, publication timing, schema assumptions, unit conversions, and coverage limits.
