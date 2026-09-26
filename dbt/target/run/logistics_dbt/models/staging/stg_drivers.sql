
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.stg_drivers
         as
        (

select
    driver_id,
    name,
    hire_date,
    region
from LOGISTICS_DB.STAGING.stg_dim_driver
        );
      
  