{{ config(materialized='table') }}

select
    e.event_id,
    e.delivery_id,
    e.event_timestamp,
    e.event_type,
    e.location_id,
    e.status

from {{ ref('stg_delivery_events') }} e

left join {{ ref('fact_delivery') }} d
    on e.delivery_id = d.delivery_id
