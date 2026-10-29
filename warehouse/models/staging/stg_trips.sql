select partition_month, trip_id, pickup_at, dropoff_at,
 pickup_zone, dropoff_zone, coalesce(vendor_id,0) as vendor_id, passenger_count,
 distance_miles, fare_usd, total_usd, payment_type, source_hash, run_id,
 extract(epoch from dropoff_at-pickup_at)/60.0 as duration_minutes,
 pickup_at::date as pickup_date,
 extract(hour from pickup_at)::integer as pickup_hour,
 (pickup_at at time zone 'America/New_York' at time zone 'UTC')::date as weather_date
from {{ source('raw','trips') }}
