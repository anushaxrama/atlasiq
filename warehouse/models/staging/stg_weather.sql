select weather_date, station, temp_c, precipitation_mm,
 case when precipitation_mm is null then 'Unknown'
 when precipitation_mm >= 1 then 'Wet' else 'Dry' end as precipitation_class,
 source_hash, day_basis
from {{ source('raw','weather') }}
