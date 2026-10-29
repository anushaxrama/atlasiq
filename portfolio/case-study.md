# AtlasIQ — Urban Mobility & Economic Activity Intelligence

**Status: In development. Verified locally; no public deployment claimed.**

## Context and problem

AtlasIQ is an independent engineering project demonstrating batch data engineering, analytics engineering, analytical SQL and software delivery. Monthly official NYC Yellow taxi records are large, imperfect and periodically revised. A useful analytical product needs reproducible extraction, trustworthy joins, clear sample boundaries and a visible path from a chart back to its source.

The operational questions are concrete: where and when do observed trips occur, how do positive fares and trip efficiency vary by zone, how do daily weather conditions align with counts, and can a reviewer trust the latest warehouse publication? Taxi records do not represent all transport demand, company profit or the whole city economy.

## Architecture and data flow

Official TLC monthly Parquet + official zone lookup + NOAA LaGuardia daily weather → SHA-256 immutable landing → deterministic bounded sample → contract/domain validation and quarantine → atomic PostgreSQL raw partition replacement → dbt staging/intermediate/star-schema/marts → quality publication gate → typed FastAPI → strict TypeScript dashboard.

Airflow orchestrates bootstrap, ingestion, transformation, validation and publication. This is intentionally monthly batch, with no Kafka or copied SignalFlow streaming code. See [architecture](../docs/ARCHITECTURE.md), [ER diagram](../docs/ER.md), [data dictionary](../docs/DATA_DICTIONARY.md), and [ADRs](../docs/ADRS.md).

## Real dataset and sampling

The verified slice uses the official January 2025 Yellow taxi file: **3,475,226 source rows** in **59,158,238 bytes**. A reproducible fingerprint-ordered 100,000-row sample produced **95,783 accepted rows** and **4,217 quarantined rows**. Raw bytes, URL, retrieval time, SHA-256, run and partition metadata are retained. Sampling is deterministic, not asserted to be a formally unbiased probability sample; counts are not expanded to population totals.

NOAA LaGuardia daily weather is converted from Fahrenheit/inches to Celsius/millimeters with missing sentinels preserved as null. TLC pickup timestamps are interpreted as NYC wall clock. Demand aggregates use local dates/hours; a derived UTC date joins the unique NOAA reporting-day dimension. This avoids weather join fanout while preserving the limitations of a single city-level station proxy.

## Warehouse and incremental behavior

The trip fact uses source month plus a source-payload fingerprint because the source has no stable trip ID. Dimensions cover local date, local hour, official pickup/dropoff zone roles, provider code and UTC daily weather. The zone lookup is Type 1, not an invented historical SCD.

Each raw month is replaced under a PostgreSQL transaction advisory lock. A failed partial load rolls back the replacement. dbt recognizes a changed active run ID, deletes that monthly fact partition and reloads it in the model transaction; revised/deleted source rows do not linger. The serving gate blocks metrics until transformations and quality checks publish every active partition.

## Product experience

The dashboard has seven functioning views: Overview, Demand Explorer, Zone Comparison, Weather & Demand, Data Quality, Pipeline Runs and Methodology. Date/zone filters, real line charts, zone drilldowns, two-zone comparisons, anomaly tables, operational pagination and empty/error/retry states consume actual FastAPI responses. API query parameters are validated and bounded; SQL is parameterized. API documentation is generated from typed Pydantic models.

## Challenges and decisions

- **No trip IDs:** exact-payload fingerprints and partition replacement, with indistinguishable legitimate duplicates/hash collisions documented.
- **Source revisions:** explicit upstream refresh and changed-partition incremental rebuilds rather than append-only duplication.
- **Invalid source rows:** quarantine with reasons and retained original bytes, plus a >10% rejection gate and review warnings.
- **Weather granularity:** one unique UTC station-day join; no invented neighborhood/hourly weather or causal inference.
- **Partial publication:** per-model dbt transactions plus an API publication barrier; a future versioned serving-schema swap could improve availability.
- **Short anomaly history:** prior same-weekday median/MAD, >=3 earlier dates, scale floor and volume threshold; flags are exploratory and not incident detection claims.

## Executed verification and actual outcomes

- Initial real ingestion accepted 95,783 sampled records in **6.508 seconds** on the recorded local ARM64/Python 3.12 environment, including extraction/reference work. This is one development-run measurement, not a production throughput guarantee or an improvement claim.
- A real Airflow `dags test` executed all **five tasks successfully**, reloaded the same partition and left the accepted/fact count unchanged.
- **28 pytest tests passed**, including a separate disposable PostgreSQL warehouse and synthetic-only test fixtures. Covered failures include 429/503/404, corrupt cache/Parquet, schema changes, duplicate reruns, partial-load rollback, source-row deletion, API limits and database outages.
- dbt built **15 models**, a calendar seed, and the documented data tests; final test counts and results are recorded in [verification](../docs/VERIFICATION.md).
- Docker API and PostgreSQL services run separately from SignalFlow. Strict Python/TypeScript checks and desktop/mobile browser checks are recorded in the verification document.
- All **12 analytical SQL files** executed and produced saved query outputs and measured durations. The generated report ranks Midtown Center highest in this sample at **4,676 observed trips**. This conclusion is conditional on the sample and exclusions.

See [queried insights](../docs/INSIGHTS.md), [raw analysis outputs](../docs/evidence/analyses.json), [run evidence](../docs/evidence/verification.json), and [measured query plan](../docs/evidence/query-plan.json). Screenshots in `screenshots/` are genuine captures of the working application. Final verification: 28 pytest tests, 17 dbt data tests, eight desktop/mobile browser journeys; the overview Lighthouse audit measured 98 Performance and 100 Accessibility/Best Practices/SEO.

## Limits and next steps

One month cannot establish seasonality. Negative/credit fare adjustments and invalid trips are excluded from the positive-trip KPI sample. NOAA GSOD 2025 archive coverage ends before a full modern backfill horizon, so newer periods need a documented successor adapter. Large full-month loads, sustained load testing, production alert delivery, cloud hosting, authenticated operations and remote CI are not verified. Next steps include migrations, versioned serving swaps, durable object storage, broader recovery tests and realistic scale experiments.
