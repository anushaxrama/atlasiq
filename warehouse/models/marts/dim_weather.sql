select to_char(weather_date,'YYYYMMDD')::integer as weather_key,* from {{ ref('stg_weather') }}
