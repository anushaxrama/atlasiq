select date,zone_id from {{ref('mart_demand_anomalies')}}
where is_unusual and (n<3 or abs(robust_score)<3.5 or greatest(observed_trips,median_trips)<10)
