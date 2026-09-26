select *
from {{ ref('fact_delivery') }}
where delivery_attempts < 1
