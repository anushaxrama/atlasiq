select a.*, z.borough,z.zone_name,d.weekday,d.weekday_name,d.is_federal_holiday,
 avg(observed_trips) over(partition by zone_id order by a.date rows between 6 preceding and current row) as rolling_7day_trips
from {{ ref('int_daily_zone') }} a
join {{ ref('dim_zone') }} z using(zone_id)
join {{ ref('dim_date') }} d on d.date=a.date
