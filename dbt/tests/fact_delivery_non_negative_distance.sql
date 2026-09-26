select *
from {{ ref('fact_delivery') }}
where distance_km < 0
