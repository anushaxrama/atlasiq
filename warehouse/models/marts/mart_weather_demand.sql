select f.weather_date,w.temp_c,w.precipitation_mm,w.precipitation_class,
 count(*) as observed_trips,avg(f.duration_minutes) as average_duration_minutes,
 avg(f.fare_usd) as average_fare_usd
from {{ ref('fct_trips') }} f
left join {{ ref('dim_weather') }} w on w.weather_key=f.weather_key
group by 1,2,3,4
