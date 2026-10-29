# Executed verification

Initial local development evidence: October 28, 2026; the multi-month extension below was verified October 29, 2026. Source/run artifacts record exact UTC timestamps. AtlasIQ remains an independent project with no hosted application deployment, professional engineering employment, or production scheduler history claimed. The public GitHub repository has passed Actions checks; see the repository for current build status.

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

- Initial evidence used one historical month; the subsequent verified backfill covers January–March with bounded samples. No full-scale or sustained throughput benchmark.
- Browser mobile emulation, not real-device Safari testing.
- Lighthouse is a local lab audit; no WCAG certification or field performance claim is made.
- No external alert delivery or cloud application deployment verified. Source is published on GitHub with passing CI history.
- Airflow tested through a real DAG execution in its own container, not a long-running production scheduler.
- Modern NOAA GSOD archive coverage may require a successor source adapter for later backfills; missing weather is not fabricated.

A FastAPI/Starlette dependency deprecation warning recommends a future test-client transport migration. Current API integration tests passed; the warning is retained rather than hidden.

## Measured overview audit

A real Lighthouse 13.6.0 mobile/simulated-throttling run against the Docker-served app measured: Performance **98**, Accessibility **100**, Best Practices **100**, Seo **100**. The JSON report is retained under `evidence/lighthouse-overview.json`. Contrast findings in the initial audit were corrected. These local laboratory scores are not field Core Web Vitals or a WCAG certification.

The final Compose-based Airflow run also completed successfully. Actual DAG/task states were extracted from its persisted metadata database into `evidence/airflow-execution.json`, with all five tasks marked success. The final Docker-served dashboard regression passed all eight browser tests.

dbt source freshness also passed for the loaded partition manifest; the actual freshness output is retained in `evidence/source-freshness.json`. It measures ingestion recency, not whether historical trip observations are current.

## Product interface refinement

The redesigned interface was rebuilt into the local API image and verified against the existing real-data warehouse. All **10 desktop/mobile Playwright checks passed**, including all seven routes, bounded filters, zone comparisons, empty states, and outage recovery. New checks verify that the seven-day shortcut selects the expected dates, the cumulative chart agrees with the filtered API total, keyboard inspection updates the chart readout, and exported CSV rows sum to that same filtered total. TypeScript build/type checks and formatting passed. Screenshots in `portfolio/screenshots/` were refreshed from the running application. Earlier Lighthouse results above describe the previous interface; they are not a measurement of this redesign.

## January–March 2025 backfill and middle-partition replay

See [machine-readable execution evidence](evidence/multi-month-backfill.json). Three official files contain **11,198,026 source rows**; selecting 100,000 records per month produced **284,899 accepted trips** and **15,101 rejected rows** across the active runs. January retained 95,783 accepted trips; February added 94,764; March added 94,352. Both the initial combined build and February replay passed all 17 dbt tests. Custom publication validation passed, with zero unmatched weather keys in each month.

Before/after comparisons verified that all three raw/fact row counts and sorted trip-ID fingerprints stayed identical on February replay, the February active run was replaced, and January/March active run IDs were preserved. The serving API reports 90 daily rows and the same 284,899-trip total. This verifies bounded multi-partition behavior, including a March DST transition, without claiming a complete DST correctness audit, unbiased sampling, city-wide demand growth, sustained throughput, or production scheduler history.

The multi-month serving regression passed **12 desktop/mobile Playwright checks** with no skips, including a January/February boundary filter and coverage-relative seven-day exports. The TypeScript build, formatting, Python type check and regenerated SQL analysis report passed.
