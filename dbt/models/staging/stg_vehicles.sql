{{ config(materialized='table') }}

select
    vehicle_id,
    type,
    capacity_kg
from {{ source('logistics_staging', 'stg_dim_vehicle') }}
