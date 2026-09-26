

select
    e.event_id,
    e.delivery_id,
    e.event_timestamp,
    e.event_type,
    e.location_id,
    e.status

from LOGISTICS_DB.ANALYTICS.stg_delivery_events e

left join LOGISTICS_DB.ANALYTICS.fact_delivery d
    on e.delivery_id = d.delivery_id