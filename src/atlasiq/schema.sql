CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE TABLE IF NOT EXISTS raw.files (
 sha256 text PRIMARY KEY, source text NOT NULL, url text NOT NULL, path text NOT NULL,
 bytes bigint NOT NULL, extracted_at timestamptz NOT NULL DEFAULT now(), content_type text,
 metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS raw.ingestion_runs (
 id uuid PRIMARY KEY, partition_month date NOT NULL, status text NOT NULL,
 started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
 source_hash text, source_rows bigint, selected_rows bigint, accepted_rows bigint,
 rejected_rows bigint, duplicate_rows bigint, sample_limit integer, elapsed_seconds double precision,
 error text, published_at timestamptz
);
CREATE TABLE IF NOT EXISTS raw.partitions (
 month date PRIMARY KEY, run_id uuid NOT NULL REFERENCES raw.ingestion_runs(id),
 source_hash text NOT NULL REFERENCES raw.files(sha256), sample_limit integer NOT NULL,
 source_rows bigint NOT NULL, accepted_rows bigint NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS raw.zones (
 location_id integer PRIMARY KEY, borough text NOT NULL, zone text NOT NULL, service_zone text,
 source_hash text NOT NULL REFERENCES raw.files(sha256)
);
CREATE TABLE IF NOT EXISTS raw.weather (
 weather_date date PRIMARY KEY, station text NOT NULL, temp_c double precision,
 precipitation_mm double precision, source_hash text NOT NULL REFERENCES raw.files(sha256),
 day_basis text NOT NULL DEFAULT 'NOAA GSOD station reporting day'
);
CREATE TABLE IF NOT EXISTS raw.trips (
 partition_month date NOT NULL, trip_id text NOT NULL, pickup_at timestamp NOT NULL,
 dropoff_at timestamp NOT NULL, pickup_zone integer NOT NULL REFERENCES raw.zones(location_id),
 dropoff_zone integer NOT NULL REFERENCES raw.zones(location_id), vendor_id integer,
 passenger_count double precision, distance_miles double precision NOT NULL,
 fare_usd double precision NOT NULL, total_usd double precision NOT NULL, payment_type integer,
 source_hash text NOT NULL REFERENCES raw.files(sha256), run_id uuid NOT NULL REFERENCES raw.ingestion_runs(id),
 PRIMARY KEY(partition_month,trip_id)
);
CREATE INDEX IF NOT EXISTS trips_pickup_idx ON raw.trips(pickup_at,pickup_zone);
CREATE TABLE IF NOT EXISTS raw.quarantine (
 run_id uuid NOT NULL REFERENCES raw.ingestion_runs(id), record_hash text NOT NULL,
 reason text NOT NULL, record jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.quality_checks (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, run_id uuid REFERENCES raw.ingestion_runs(id),
 checked_at timestamptz NOT NULL DEFAULT now(), check_name text NOT NULL,
 status text NOT NULL CHECK(status IN ('pass','warning','fail')), observed double precision,
 threshold text NOT NULL, details jsonb NOT NULL DEFAULT '{}'
);
