{{ config(materialized='table') }}

select
    driver_id,
    name,
    hire_date,
    region
from {{ source('logistics_staging', 'stg_dim_driver') }}
