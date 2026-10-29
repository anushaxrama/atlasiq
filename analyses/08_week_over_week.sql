-- Question: which same-weekday zone counts changed vs seven calendar days prior?
-- Output: date, zone_name, observed_trips, prior_week_trips, percent_change. Prior zero stays undefined.
select a.date,a.zone_name,a.observed_trips,b.observed_trips as prior_week_trips,
100.0*(a.observed_trips-b.observed_trips)/nullif(b.observed_trips,0) as percent_change
from marts.mart_daily_zone a join marts.mart_daily_zone b on b.zone_id=a.zone_id and b.date=a.date-7
where a.observed_trips>=20 order by abs(100.0*(a.observed_trips-b.observed_trips)/nullif(b.observed_trips,0)) desc nulls last limit 30;
