-- Question: what is each zone's recent seven-calendar-day observed pattern?
-- Output: date, zone_name, observed_trips, rolling_7day_trips; zero-filled modeled dates only.
select date,zone_name,observed_trips,rolling_7day_trips from marts.mart_daily_zone
where zone_id in (select pickup_zone from marts.fct_trips group by 1 order by count(*) desc limit 3)
order by zone_name,date;
