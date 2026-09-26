
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.dim_location
         as
        (

select
    location_id,
    city,
    zone,
    latitude,
    longitude
from LOGISTICS_DB.ANALYTICS.stg_locations
        );
      
  