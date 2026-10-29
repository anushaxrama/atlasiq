# Logical star schema

```mermaid
erDiagram
 DIM_DATE ||--o{ FCT_TRIPS : pickup_date
 DIM_TIME ||--o{ FCT_TRIPS : pickup_hour
 DIM_ZONE ||--o{ FCT_TRIPS : pickup_zone
 DIM_ZONE ||--o{ FCT_TRIPS : dropoff_zone
 DIM_WEATHER o|--o{ FCT_TRIPS : utc_reporting_date
 DIM_VENDOR ||--o{ FCT_TRIPS : provider_code
 RAW_PARTITIONS ||--o{ FCT_TRIPS : month
 RAW_RUNS ||--o{ RAW_PARTITIONS : active_run
 RAW_FILES ||--o{ RAW_TRIPS : provenance
 RAW_RUNS ||--o{ RAW_QUARANTINE : rejected_rows
 FCT_TRIPS {
   date partition_month PK
   string trip_id PK
   timestamp pickup_at
   timestamp dropoff_at
   integer date_key
   integer hour_key
   integer pickup_zone
   integer dropoff_zone
   integer weather_key
   integer vendor_id
   float distance_miles
   float fare_usd
   float duration_minutes
   uuid run_id
 }
```

Raw primary/foreign keys are enforced in PostgreSQL. dbt analytical relationships are tested rather than advertised as declared physical FKs. `dim_zone` is the current official lookup (Type 1 overwrite); no invented historical SCD effective dates. `dim_weather` is unique by station reporting date. A nullable weather key retains trips with unknown weather and prevents implicit row loss. Unknown/outside-NYC official zone codes remain labeled.
