select location_id as zone_id, borough, zone as zone_name, service_zone, source_hash
from {{ source('raw','zones') }}
