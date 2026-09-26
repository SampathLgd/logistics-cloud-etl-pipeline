
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.stg_locations
         as
        (

select
    location_id,
    city,
    zone,
    latitude,
    longitude
from LOGISTICS_DB.STAGING.stg_dim_location
        );
      
  