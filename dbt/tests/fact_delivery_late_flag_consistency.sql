select *
from {{ ref('fact_delivery') }}
where actual_delivery_time is not null
  and is_late != (delay_minutes > 15)
