select 'daily_count_mismatch' as failure where
(select sum(observed_trips) from {{ref('mart_daily_zone')}}) <>
(select count(*) from {{ref('fct_trips')}})
