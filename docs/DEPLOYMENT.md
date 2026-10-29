# Deployment readiness and troubleshooting

No public AtlasIQ deployment or remote GitHub repository URL is claimed. Local Compose and a full Airflow DAG test are verified. Public deployment needs an approved host, credentials, storage/backups and operating budget; do not provision paid services without approval.

A production deployment needs a PostgreSQL instance, durable raw landing storage, a batch scheduler, and a FastAPI serving process. Build the frontend first, then the application image. Configure ATLAS_DATABASE_URL and ATLAS_DATA_DIR privately. Replace local-only credentials and use TLS/private network access. Bind the API behind HTTPS; keep the warehouse unexposed publicly. Run migrations/bootstrap deliberately; the current version has additive bootstrap DDL rather than a complete migration framework.

The portfolio dashboard is read-only. Operational endpoints reveal run and source metadata; add appropriate authentication/rate limits before exposing internal operations in production. Set conservative database connection limits and request concurrency; a simple synchronous per-query connection is appropriate for the local project but not a high-concurrency pool implementation. No paid hosting, secrets or analytics tracking has been activated.

Common issues:
- Port 5544/8020/8082 busy: inspect the AtlasIQ services or native server. Do not stop unrelated SignalFlow services.
- Analytics 503 but health 200: ingest and transform the source month, inspect quality failures, then publish.
- Missing dbt command: activate the project's uv environment; Airflow intentionally uses its own isolated application venv.
- A later 2025 NOAA month has insufficient coverage: preserve the failed/unknown results and implement a documented NOAA successor adapter; do not relabel missing observations as dry weather.
- A new field appears: additive fields are recorded as schema metadata; required-field removal fails. Inspect data types and domain changes before accepting them.
- Tests skipped: set TEST_ATLAS_DATABASE_URL to a separate database named atlasiq_test. Production data must never be a test target.
- Generated frontend assets missing: run `pnpm install --frozen-lockfile && pnpm build` before starting/building the app.

Future work: versioned serving-schema swaps, explicit migrations, object-storage deployment, a station-source successor for modern backfills, larger-scale benchmarks, richer spatial geometry, and broader scheduler/crash fault injection. These are limitations/next steps rather than finished features.
