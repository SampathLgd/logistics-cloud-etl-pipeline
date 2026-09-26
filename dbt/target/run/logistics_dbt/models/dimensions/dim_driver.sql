
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.dim_driver
         as
        (

select
    driver_id,
    name,
    hire_date,
    region
from LOGISTICS_DB.ANALYTICS.stg_drivers
        );
      
  