{{ config(materialized='incremental', unique_key=['partition_month','trip_id'],
  pre_hook="{% if is_incremental() %}delete from {{ this }} where partition_month in (select p.month from raw.partitions p where not exists (select 1 from {{ this }} f where f.partition_month=p.month and f.run_id=p.run_id)){% endif %}",
  post_hook=["create index if not exists atlas_fact_date_zone on {{ this }}(pickup_date,pickup_zone)","create index if not exists atlas_fact_weather on {{ this }}(weather_date)"]) }}
select t.*,to_char(t.pickup_date,'YYYYMMDD')::integer as date_key,
 t.pickup_hour as hour_key, w.weather_key,
 case when duration_minutes>0 then distance_miles/duration_minutes*60 end as average_mph,
 current_timestamp as modeled_at
from {{ ref('stg_trips') }} t
left join {{ ref('dim_weather') }} w on w.weather_date=t.weather_date
{% if is_incremental() %}
where t.partition_month in (select p.month from {{ source('raw','partitions') }} p
 where not exists(select 1 from {{this}} f where f.partition_month=p.month and f.run_id=p.run_id))
{% endif %}
