# AtlasIQ implementation checklist

- [x] Inspect existing workspace; isolate AtlasIQ from SignalFlow and its database.
- [x] Verify TLC source documentation, monthly/two-month-lag cadence and 2025 congestion-fee schema addition.
- [x] Inspect downloaded Parquet schema and official zone/weather contracts.
- [x] Prove a real partition → PostgreSQL → dbt → FastAPI → dashboard vertical slice.
- [x] Add atomic partition replacement, deduplication, quarantine, audit and quality gates.
- [x] Complete dimensions, incremental facts, aggregates and 12 documented SQL analyses.
- [x] Add Airflow orchestration, failure/recovery checks and runbook.
- [x] Finish dashboard, typed API, tests, measured evidence and portfolio artifacts.

Architecture: official monthly TLC Parquet + official TLC zones + NOAA historical daily weather + US federal holiday rules → immutable SHA-256 landing files → deterministic bounded sample and validation → transactional PostgreSQL raw partition replacement → dbt staging/intermediate/dimensional marts → read-only FastAPI → accessible dashboard.

Use DuckDB only to scan/sample Parquet efficiently; PostgreSQL remains the warehouse and dbt performs business transformations. Choose a lean TypeScript dashboard so implementation effort stays on batch reliability and warehouse semantics. No Kafka, no copied SignalFlow code, no paid infrastructure, no public deployment without approval.
