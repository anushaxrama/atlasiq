# Verified January–March 2025 backfill

The local warehouse was extended from January to February and March using the official monthly Yellow taxi Parquet files. Each month selects up to 100,000 deterministic bottom-k payload fingerprints before validation. These are observed samples, not estimates of the whole city.

| Partition | Original source rows | Selected | Accepted | Rejected |
|---|---:|---:|---:|---:|
| January 2025 | 3,475,226 | 100,000 | 95,783 | 4,217 |
| February 2025 | 3,577,543 | 100,000 | 94,764 | 5,236 |
| March 2025 | 4,145,257 | 100,000 | 94,352 | 5,648 |
| Total | 11,198,026 | 300,000 | 284,899 | 15,101 |

Rejection counts describe each active partition's run, not the cumulative quarantine ledger across replays. Rejection-rate warnings remain visible; no blocking publication checks failed. All facts matched a NOAA weather reporting date. The March partition includes the spring DST transition, but this run does not by itself prove every DST edge case.

## Reproduce

After completing the one-month quickstart and starting the API container:

```sh
# Extend the existing January warehouse; month boundaries are inclusive.
docker compose exec api atlasiq backfill --start 2025-02 --end 2025-03 --limit 100000
# Replay the middle partition, then rebuild/test and publish.
docker compose exec api atlasiq demo --month 2025-02 --limit 100000
```

For a fresh warehouse, use the same `backfill` command with `--start 2025-01`. Native development uses `uv run atlasiq` in place of `docker compose exec api atlasiq`. Downloads and local database volumes are ignored by Git.

During a new raw load, analytics intentionally return 503 until transformation, quality gates and publication succeed. The run ledger remains available. A failure in a later month retains earlier committed loads; correct the failure and retry the affected range.

## What was verified

The [execution record](evidence/multi-month-backfill.json) contains before-backfill, after-backfill and after-February-replay snapshots; source URLs, byte lengths and SHA-256 checksums; active run IDs; raw/fact row counts and sorted trip-ID fingerprints; weather matching; and actual dbt statuses.

- January's accepted count and trip-ID fingerprint stayed unchanged when new months were added.
- Replaying February replaced its active run, preserving January/March active run IDs.
- All three raw/fact counts and trip-ID fingerprints stayed identical after the replay: **284,899 total**.
- Both combined builds passed **17 dbt tests**, plus the publication validation gates.
- Serving results reconcile to **90 pickup dates**, January 1–March 31, 2025.
- Browser checks exercise cross-month filtering, date shortcuts, chart inspection, comparison and CSV totals on desktop and mobile.

Trip-ID fingerprints verify identity sets, not every transformed value. The retained source hashes identify the exact original files. This is a bounded local execution, not a production-scale load or sustained scheduler test.

## Interpreting the wider dataset

A fixed 100,000-record selection means sampled monthly totals are artificially capped. Do not interpret differences in accepted sample counts as changes in total NYC demand. The original source row counts are useful source-volume context but include records subsequently excluded from KPI analysis. Rejection rates and deterministic selection can change the distribution. Three historical months cannot establish annual seasonality or causality.

The original one-month evidence remains historical evidence in the verification document. Regenerated analytical results and dashboard screenshots describe the expanded local warehouse. A fresh clone still needs to ingest the public data; the GitHub repository does not contain the raw files or a prepopulated database.
