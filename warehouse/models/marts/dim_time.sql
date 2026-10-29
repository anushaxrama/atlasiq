select hour as hour_key,
 case when hour between 6 and 9 then 'Morning' when hour between 10 and 15 then 'Daytime'
 when hour between 16 and 19 then 'Evening' else 'Night' end as day_period
from generate_series(0,23) hour
