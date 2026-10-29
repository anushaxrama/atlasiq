-- Question: how does observed provider-code composition vary across local dates?
-- Output: pickup_date, vendor_id, observed_trips, within_day_share. Provider codes are not company profitability.
with counts as(select pickup_date,vendor_id,count(*) as observed_trips from marts.fct_trips group by 1,2)
select *,observed_trips::numeric/sum(observed_trips) over(partition by pickup_date) as within_day_share
from counts order by pickup_date,vendor_id;
