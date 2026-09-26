{{ config(materialized='table') }}

select
    location_id,
    city,
    zone,
    latitude,
    longitude
from {{ ref('stg_locations') }}
