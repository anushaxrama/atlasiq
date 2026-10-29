-- Question: how do local daily counts differ on federal observed holidays?
-- Output: is_federal_holiday, days, mean_daily_observed_trips. No matched counterfactual; holiday flags are limited.
with daily as (select pickup_date,count(*) as trips from marts.fct_trips group by 1)
select d.is_federal_holiday,count(*) as days,avg(t.trips) as mean_daily_observed_trips
from daily t join marts.dim_date d on d.date=t.pickup_date group by 1;
