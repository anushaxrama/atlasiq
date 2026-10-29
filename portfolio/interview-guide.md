# AtlasIQ interview guide

**Why batch?** The primary source is published monthly with roughly two months' delay. Streaming infrastructure cannot make that source live. A monthly DAG and explicit backfills fit source cadence and reduce needless complexity.

**Why Airflow and dbt?** Airflow manages stage dependencies/retries/timeouts and execution history; dbt owns warehouse SQL, model lineage, contracts/tests and incremental fact semantics. They are complementary. Airflow's application venv isolates dbt/psycopg dependencies from Airflow 2's SQLAlchemy constraints.

**Why DuckDB plus PostgreSQL?** DuckDB efficiently scans Parquet and selects bounded records locally; PostgreSQL supplies transactional storage, SQL relationships and the dbt serving warehouse. DuckDB is not presented as a second production warehouse.

**How do you deduplicate without trip IDs?** Hash the pinned DuckDB serialization of the complete source row. Month plus fingerprint is the raw/fact key. This detects exact repeats; identical legitimate trips and theoretical MD5 collisions cannot be resolved from unavailable source IDs. Do not claim business-event exactly-once semantics.

**What happens on revisions/deletions?** Fetch revised immutable source bytes explicitly, transactionally replace the raw month, then let the active run ID drive deletion/reload of that fact month. Tests remove fixture rows and verify old facts vanish. Merely upserting new IDs would leave deleted facts behind.

**What if loading crashes?** The run is marked failed outside the replacement transaction. The old active partition survives rollback. Source files remain immutable and hashed. Retry the same month. A >10% rejection fraction fails the replacement; warnings and quarantine still need review.

**What is the model grain?** One accepted source-payload identity per month in fct_trips. Pickup/dropoff use the same official zone dimension in different roles. Daily marts are date×zone; hourly marts are date×hour×zone; weather is one UTC reporting-day proxy. Explain why every join needs a declared grain.

**How do weather joins avoid double counting?** Derive a UTC reporting date from NYC-local pickup time and join a unique weather row. A left join retains unknown weather. dbt checks overall fact/raw reconciliation and weather-key uniqueness. Daily GSOD station observations are not hourly neighborhood measurements.

**How is publication reliable?** Raw replacement is atomic; dbt is transactional per model, not per entire project. While an active partition is unpublished, metric endpoints return readiness 503 rather than promising a consistent new version. Versioned serving schemas/view swaps are a future availability improvement.

**What do tests prove?** Synthetic fixtures validate contracts/replay/revisions/rollback and typed API boundaries without source-network dependence. Real-data execution validates the selected current source slice. Airflow dags test verifies all five tasks, not a production scheduler history. Browser tests exercise real running API views and error recovery. CI configuration is not proof of remote CI execution.

**How is unusual demand detected?** Prior same-weekday medians/MAD over 56 days, at least three prior dates, a two-trip scale floor, absolute score >=3.5 and a volume >=10 condition. One month has limited history and sample noise, so flags are exploratory. No incident classifier or causality claim is made.

**What did performance measurements show?** Discuss the recorded initial 6.508-second bounded ingestion and actual EXPLAIN ANALYZE/BUFFERS artifact. Timings include local connection/extraction work, depend on cache/machine and are not cloud production latency. There is no before/after improvement claim without a controlled baseline.

**What would you change for production?** Explicit migrations, connection pooling/concurrency limits, versioned serving schemas, object-storage retention/backups, private operations/auth/rate limits, modern weather-source coverage, larger full-partition benchmarks, production scheduler history and tested external alerts. State what remains unverified.
