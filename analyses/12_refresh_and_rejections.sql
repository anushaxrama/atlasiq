-- Question: how much source data was scanned, accepted, quarantined and modeled in each active partition?
-- Output: month, source_rows, accepted_rows, rejected_rows, modeled_rows, sample_fraction, elapsed_seconds, rejection_rate.
-- Refresh age describes processing recency, not current trip activity.
select month,source_rows,accepted_rows,rejected_rows,modeled_rows,
accepted_rows::numeric/nullif(source_rows,0) as sample_fraction,elapsed_seconds,
rejected_rows::numeric/nullif(accepted_rows+rejected_rows,0) as rejection_rate
from marts.mart_refresh_health order by month;
