-- Question: how do daily observed counts compare on wet and dry reporting days?
-- Output: precipitation_class, reporting_days, mean_daily_observed_trips, mean_duration.
-- UTC weather dates at local-month edges may be partial; no causal interpretation.
select precipitation_class,count(*) as reporting_days,avg(observed_trips) as mean_daily_observed_trips,
avg(average_duration_minutes) as mean_duration from marts.mart_weather_demand group by 1;
