# Executed verification

Local development evidence, October 28, 2026 (source/run artifacts record exact UTC timestamps). AtlasIQ remains in development. No public deployment, professional engineering employment, production scheduler history or remote GitHub Actions success is claimed.

## Real source slice

- Official January 2025 TLC Yellow file: **59,158,238 bytes**, **3,475,226 source rows**.
- SHA-256: `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a`.
- Deterministic selected sample: **100,000 rows**. Accepted **95,783**, quarantined **4,217**, duplicate rows **0** in this selected source slice.
- Initial measured ingestion: **6.5076 seconds**, including download/reference work, on the recorded local macOS ARM64 / Python 3.12 environment. A real Airflow replay took **7.2139 seconds** and preserved the same accepted active partition count. Do not interpret these as production throughput or a before/after improvement.
- All 12 analytical SQL files executed; outputs/timings and EXPLAIN ANALYZE/BUFFERS are retained under `evidence/`. Insights and chart are generated from those results.

## Automated execution

- Python contracts/unit/integration/API/recovery suite: **28 passed**, with an explicit separate `atlasiq_test` database and synthetic test-only fixtures. Tests included HTTP unavailable/rate-limited/missing sources, bad content types, corrupted cache/Parquet, schema change, duplicate replay, partial-load rollback and source-row deletions.
- Strict Python checking (`mypy src`) and Ruff lint/format: passed during implementation; rerun final commands after edits.
- Strict TypeScript dashboard build: passed.
- dbt: **15 models**, one calendar seed and **16 tests** passed in the initial real-data build. The final production build passed **17 tests** after adding the anomaly-method contract.
- Docker application and Airflow images built. The API and PostgreSQL run as AtlasIQ Compose services, with the original data volume preserved.
- Airflow `dags test atlasiq_monthly` with explicit January/100000 configuration: **all five tasks succeeded** (bootstrap, ingest, transform, validate, publish). This is a full task execution test, not an actual production scheduled run.
- All **8 desktop/mobile Playwright journeys passed** across the seven views, real API filters, comparisons, empty states and error/retry behavior. Initial tests caught an implicit select-label mismatch; an explicit accessible label corrected it.

## Verification limits

- One historical month and bounded sample; no full-scale or sustained throughput benchmark.
- Browser mobile emulation, not real-device Safari testing.
- Lighthouse is a local lab audit; no WCAG certification or field performance claim is made.
- No external alert delivery, cloud deployment, public repository or remote CI run verified.
- Airflow tested through a real DAG execution in its own container, not a long-running production scheduler.
- Modern NOAA GSOD archive coverage may require a successor source adapter for later backfills; missing weather is not fabricated.

A FastAPI/Starlette dependency deprecation warning recommends a future test-client transport migration. Current API integration tests passed; the warning is retained rather than hidden.

## Measured overview audit

A real Lighthouse 13.6.0 mobile/simulated-throttling run against the Docker-served app measured: Performance **98**, Accessibility **100**, Best Practices **100**, Seo **100**. The JSON report is retained under `evidence/lighthouse-overview.json`. Contrast findings in the initial audit were corrected. These local laboratory scores are not field Core Web Vitals or a WCAG certification.

The final Compose-based Airflow run also completed successfully. Actual DAG/task states were extracted from its persisted metadata database into `evidence/airflow-execution.json`, with all five tasks marked success. The final Docker-served dashboard regression passed all eight browser tests.

dbt source freshness also passed for the loaded partition manifest; the actual freshness output is retained in `evidence/source-freshness.json`. It measures ingestion recency, not whether historical trip observations are current.
