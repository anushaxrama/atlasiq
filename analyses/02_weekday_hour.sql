-- Question: how does observed pickup intensity vary by local weekday/hour?
-- Output: weekday, pickup_hour, observed_trips, trips_per_covered_day. Sampling is not population demand.
select d.weekday,f.pickup_hour,count(*) as observed_trips,
 count(*)::numeric/count(distinct f.pickup_date) as trips_per_covered_day
from marts.fct_trips f join marts.dim_date d using(date_key)
group by 1,2 order by 1,2;
