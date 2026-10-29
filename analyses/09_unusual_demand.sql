-- Question: which observations exceed the documented prior same-weekday median/MAD threshold?
-- Output: date, zone_name, observed_trips, median_trips, mad, n, robust_score. Flags are exploratory.
select date,zone_name,observed_trips,median_trips,mad,n,robust_score
from marts.mart_demand_anomalies where is_unusual order by abs(robust_score) desc limit 30;
