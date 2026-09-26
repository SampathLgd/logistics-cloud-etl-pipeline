{{ config(materialized='table') }}

select
    location_id,
    city,
    zone,
    latitude,
    longitude
from {{ source('logistics_staging', 'stg_dim_location') }}
