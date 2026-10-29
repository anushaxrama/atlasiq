select to_char(d,'YYYYMMDD')::integer as date_key,d::date as date,
 extract(isodow from d)::integer as weekday, to_char(d,'Dy') as weekday_name,
 extract(month from d)::integer as month, extract(year from d)::integer as year,
 extract(isodow from d) in (6,7) as is_weekend,
 h.holiday_date is not null as is_federal_holiday, h.holiday_name
from {{ source('raw','partitions') }} p
cross join lateral generate_series(p.month,p.month+interval '1 month'-interval '1 day',interval '1 day') d
left join {{ ref('federal_holidays') }} h on h.holiday_date::date=d::date
