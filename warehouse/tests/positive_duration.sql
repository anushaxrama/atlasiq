select trip_id from {{ref('fct_trips')}} where duration_minutes<=0 or duration_minutes>360
