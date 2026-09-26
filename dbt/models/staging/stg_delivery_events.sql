{{ config(materialized='table') }}

select
    event_id,
    delivery_id,
    event_timestamp,
    event_type,
    location_id,
    status
from {{ source('logistics_staging', 'stg_fact_delivery_event') }}
