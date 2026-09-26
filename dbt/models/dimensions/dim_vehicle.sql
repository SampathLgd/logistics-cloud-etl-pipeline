{{ config(materialized='table') }}

select
    vehicle_id,
    type as vehicle_type,
    capacity_kg
from {{ ref('stg_vehicles') }}
