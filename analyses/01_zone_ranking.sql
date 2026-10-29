-- Question: which official pickup zones have the most accepted sampled trips?
-- Output: zone_name, borough, observed_trips, demand_rank. No city-wide extrapolation.
with counts as (select pickup_zone,count(*) as observed_trips from marts.fct_trips group by 1)
select z.zone_name,z.borough,c.observed_trips,dense_rank() over(order by c.observed_trips desc) as demand_rank
from counts c join marts.dim_zone z on z.zone_id=c.pickup_zone order by demand_rank limit 20;
