# AtlasIQ project summaries

## 100-word summary

AtlasIQ is a batch data platform that connects NYC Yellow taxi records, zone lookup data, NOAA weather and a federal calendar. Immutable source files feed validated, transaction-safe PostgreSQL partitions, then dbt dimensions and analytical marts. A typed FastAPI service powers a strict TypeScript dashboard with demand exploration, zone comparisons, weather associations and quality/run history. The verified sample scanned 3,475,226 source rows and accepted 95,783 from 100,000 selected records. Tests cover duplicates, revisions, partial failures and API boundaries. A five-task Airflow DAG test passed. Findings remain explicitly limited to sampled observations; fares are not profit and weather comparisons are not causal.

## 250-word summary

AtlasIQ — Urban Mobility & Economic Activity Intelligence is an engineering project for batch analytics. It turns official monthly NYC TLC Yellow taxi Parquet records, zones, NOAA LaGuardia weather and a federal holiday calendar into an inspectable warehouse and analytical product.

The pipeline downloads files with bounded retries, content validation and SHA-256 provenance. DuckDB selects a reproducible sample; Python validates records and retains invalid examples in quarantine. PostgreSQL transactions and partition locks replace a month safely. Repeated runs do not add duplicate trips, and a failed partial load preserves the prior partition.

The dbt warehouse separates raw, staging, intermediate and marts. An incremental trip fact joins date, time, zone, provider and daily weather dimensions. Changed partition run IDs trigger deletion and reload so removed or revised rows do not survive. Relationship and reconciliation tests protect the model, while a publication gate blocks analytical serving until checks pass.

A typed FastAPI service powers seven TypeScript dashboard views. Users can explore daily/hourly demand, compare official pickup zones, inspect descriptive weather relationships, investigate exploratory median/MAD flags, and review quality checks and pipeline history. Twelve SQL analyses generate saved results, measured query plans, an insights narrative and a real-data chart.

The January slice scanned 3,475,226 source records, accepted 95,783 of 100,000 selected rows and quarantined 4,217. A full five-task Airflow DAG test and separate-database recovery tests passed. All measurements are local and conditional on sampling and exclusions. The project is in development; no production deployment, city-wide demand estimate or causal weather effect is claimed.
