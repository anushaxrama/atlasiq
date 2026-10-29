select distinct vendor_id, 'TLC provider code '||vendor_id as vendor_label, 'Yellow taxi' as trip_type
from {{ ref('stg_trips') }}
