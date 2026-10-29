-- Question: which zones have longer observed trips or slower per-trip average speeds?
-- Output: zone_name, observed_trips, average_duration_minutes, average_distance_miles, average_mph; >=100 sampled trips.
select z.zone_name,e.observed_trips,e.average_duration_minutes,e.average_distance_miles,e.average_mph
from marts.mart_trip_efficiency e join marts.dim_zone z on z.zone_id=e.pickup_zone
where e.observed_trips>=100 order by average_duration_minutes desc limit 20;
