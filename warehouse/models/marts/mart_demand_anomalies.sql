with baselines as (
 select a.*, b.n,b.median_trips
 from {{ ref('mart_daily_zone') }} a
 cross join lateral(select count(*) as n,percentile_cont(.5) within group(order by observed_trips) as median_trips
 from {{ ref('mart_daily_zone') }} p where p.zone_id=a.zone_id and p.weekday=a.weekday
 and p.date<a.date and p.date>=a.date-interval '56 days') b
), deviations as (
 select a.*,m.mad
 from baselines a cross join lateral (
 select percentile_cont(.5) within group(order by abs(p.observed_trips-a.median_trips)) as mad
 from {{ ref('mart_daily_zone') }} p where p.zone_id=a.zone_id and p.weekday=a.weekday
 and p.date<a.date and p.date>=a.date-interval '56 days') m
)
select *, (observed_trips-median_trips)/greatest(1.4826*mad,2) as robust_score,
 n>=3 and abs(observed_trips-median_trips)/greatest(1.4826*mad,2)>=3.5
 and greatest(observed_trips,median_trips)>=10 as is_unusual
from deviations
