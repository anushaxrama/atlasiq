select pickup_zone,count(*) as observed_trips,avg(distance_miles) as average_distance_miles,
 avg(duration_minutes) as average_duration_minutes,avg(average_mph) as average_mph,
 percentile_cont(.5) within group(order by fare_usd) as median_fare_usd,
 percentile_cont(.9) within group(order by fare_usd) as p90_fare_usd
from {{ ref('fct_trips') }} group by 1
