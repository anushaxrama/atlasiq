select p.*,r.status,r.rejected_rows,r.duplicate_rows,r.elapsed_seconds,
 r.accepted_rows/nullif(r.elapsed_seconds,0) as accepted_rows_per_second,
 (select count(*) from {{ref('fct_trips')}} f where f.partition_month=p.month) as modeled_rows
from {{source('raw','partitions')}} p join raw.ingestion_runs r on p.run_id=r.id
