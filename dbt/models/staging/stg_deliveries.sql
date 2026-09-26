{{ config(materialized='table') }}

select
    delivery_id,
    driver_id,
    vehicle_id,
    pickup_location_id,
    delivery_location_id,
    scheduled_pickup_time,
    actual_pickup_time,
    scheduled_delivery_time,
    actual_delivery_time,
    delivery_status,
    delivery_attempts,
    distance_km,
    delivery_duration_minutes,
    delay_minutes,
    is_late,
    distance_bucket,
    delivery_hour,
    delivery_day,
    delivery_week
from {{ source('logistics_staging', 'stg_fact_delivery') }}
