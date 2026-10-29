select pickup_date,pickup_hour,pickup_zone,count(*) as observed_trips,
 avg(duration_minutes) as average_duration_minutes,avg(fare_usd) as average_fare_usd
from {{ ref('fct_trips') }} group by 1,2,3
