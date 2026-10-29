-- Question: which pickup/dropoff borough pairs are common in accepted sampled records?
-- Output: pickup_borough, dropoff_borough, observed_trips, flow_share. Not entire mobility market.
with flows as (select p.borough as pickup_borough,d.borough as dropoff_borough,count(*) as observed_trips
from marts.fct_trips f join marts.dim_zone p on p.zone_id=f.pickup_zone
join marts.dim_zone d on d.zone_id=f.dropoff_zone group by 1,2)
select *,observed_trips::numeric/sum(observed_trips) over() as flow_share from flows order by observed_trips desc;
