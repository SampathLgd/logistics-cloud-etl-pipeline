{{ config(materialized='table') }}

select
    d.delivery_id,

    dr.driver_id,
    v.vehicle_id,

    d.pickup_location_id,
    d.delivery_location_id,

    d.scheduled_pickup_time,
    d.actual_pickup_time,
    d.scheduled_delivery_time,
    d.actual_delivery_time,

    d.delivery_status,
    d.delivery_attempts,
    d.distance_km,
    d.delivery_duration_minutes,
    d.delay_minutes,
    d.is_late,
    d.distance_bucket,
    d.delivery_hour,
    d.delivery_day,
    d.delivery_week

from {{ ref('stg_deliveries') }} d

left join {{ ref('dim_driver') }} dr
    on d.driver_id = dr.driver_id

left join {{ ref('dim_vehicle') }} v
    on d.vehicle_id = v.vehicle_id

left join {{ ref('dim_location') }} pickup
    on d.pickup_location_id = pickup.location_id

left join {{ ref('dim_location') }} delivery
    on d.delivery_location_id = delivery.location_id
