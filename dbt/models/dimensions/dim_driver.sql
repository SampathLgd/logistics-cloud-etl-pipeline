{{ config(materialized='table') }}

select
    driver_id,
    name,
    hire_date,
    region
from {{ ref('stg_drivers') }}
