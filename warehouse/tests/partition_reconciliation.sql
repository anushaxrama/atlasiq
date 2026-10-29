select p.month from raw.partitions p left join {{ref('fct_trips')}} f on f.partition_month=p.month
group by p.month,p.accepted_rows having count(f.trip_id)<>p.accepted_rows
