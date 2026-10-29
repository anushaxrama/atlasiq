# Operational runbook

## Normal refresh

1. Confirm the official TLC monthly file exists and NOAA station archive covers the requested reporting dates. TLC normally publishes about two months behind; GSOD's 2025 archive does not continue indefinitely, so later months can require a documented successor-source adapter.
2. Ingest `--month YYYY-MM --limit 100000` (or deliberately choose a full load). Extraction creates immutable byte-hashed files; a URL pointer is only a cache reference.
3. Inspect `raw.ingestion_runs`, `raw.quality_checks`, and reason counts in `raw.quarantine`. Rejection >10% fails the load; >=2% warns. Duplicate rate >=1%, >25% accepted-row change and partial sampling are explicit review warnings.
4. Run `transform` (calendar seed + dbt build/tests). Facts replace changed monthly partitions, preserving unchanged partitions.
5. Run `validate`, then `publish`. Analytics open only when every active raw partition is published. Warnings are retained; only blocking failures prevent publication. Inspect `/api/quality`, `/api/runs` and readiness.
6. Generate insights and preserve evidence when documenting results. Never confuse load freshness with trip-date recency.

## Backfills and late source revisions

`atlasiq backfill --start 2025-01 --end 2025-02 --limit 100000` walks inclusive monthly partitions, then transforms/publishes. For a revised upstream file, use `ingest --refresh` for that month first, then transform/validate/publish. Successful raw loads are durable even if a later month fails; retry the failed range. No uncontrolled full-history automatic catchup is enabled.

Same-partition concurrency is serialized with a transaction advisory lock. Atomic raw replacement leaves the prior committed partition visible during load. The serving publication gate closes once a newly loaded partition is active, avoiding partially updated marts. Retry operations use stable month identities and do not add duplicate facts. Per-run quarantined records are intentionally historical audit entries and can repeat across reruns.

## Failure handling

| Failure | Evidence | Recovery |
| --- | --- | --- |
| HTTP 429/temporary 5xx | Source/run logs, bounded retries | Respect Retry-After; retry the same month after the source recovers |
| 404/missing partition | Failed run, no destructive replacement | Check publication cadence and month; do not substitute fake records |
| Corrupt cached file | Checksum failure | Preserve suspicious bytes for diagnosis; explicitly refresh after review |
| Schema drift | Missing required-field error | Inspect source dictionary, update contract with tests; don't silently drop fields |
| Invalid rows | Quarantine reason and original landing bytes | Review thresholds and business exclusions before rerunning |
| Mid-load crash/exception | Failed run; old active partition survives | Retry same partition; transaction rollback is tested |
| dbt/test failure | dbt logs, quality checks, readiness 503 | Correct transformation/data issue; rerun transform/validate/publish |
| Database unavailable | API 503, health failure | Restore isolated database service/volume; retry; errors don't expose credentials |

Airflow retries tasks twice with exponential retry delays and timeouts. The failure callback writes structured actionable log records; no email/Slack delivery is configured or claimed. To add notifications, configure an approved connection/secret and test delivery before claiming it works.

## Storage, retention and bounds

Raw files and PostgreSQL volumes are local, ignored by Git, and not automatically deleted. Plan disk retention/backups before a large backfill. Default Parquet downloads have a 2 GB safety bound, 90-second read timeout and four attempts. API date ranges cap at 367 inclusive calendar days; pagination caps at 100 rows (265 for zone lists). SQL statement timeout is 30 seconds. Full-month loading keeps a deduplication set in memory, so size the environment deliberately.

Back up before destructive database/volume commands. `docker compose down` preserves named volumes; do not run `down -v` unless intentionally discarding this project's data. SignalFlow uses separate services/ports and must remain untouched.
