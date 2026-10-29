select partition_month,trip_id from {{ref('fct_trips')}} group by 1,2 having count(*)>1
