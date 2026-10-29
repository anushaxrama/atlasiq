-- Question: how do positive observed fare distributions differ by borough?
-- Output: borough, trips, median_fare_usd, p90_fare_usd, p99_fare_usd. Negative/credit rows quarantined; not profit.
select z.borough,count(*) as trips,percentile_cont(.5) within group(order by f.fare_usd) as median_fare_usd,
percentile_cont(.9) within group(order by f.fare_usd) as p90_fare_usd,
percentile_cont(.99) within group(order by f.fare_usd) as p99_fare_usd
from marts.fct_trips f join marts.dim_zone z on z.zone_id=f.pickup_zone group by 1 order by trips desc;
