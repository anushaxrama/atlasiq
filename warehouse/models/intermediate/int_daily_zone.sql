select d.date,z.zone_id, count(f.trip_id)::bigint as observed_trips,
 avg(f.distance_miles) as average_distance_miles,avg(f.duration_minutes) as average_duration_minutes,
 sum(f.fare_usd) as observed_fare_usd,avg(f.average_mph) as average_mph
from {{ ref('dim_date') }} d cross join {{ ref('dim_zone') }} z
left join {{ ref('fct_trips') }} f on f.pickup_date=d.date and f.pickup_zone=z.zone_id
group by 1,2
