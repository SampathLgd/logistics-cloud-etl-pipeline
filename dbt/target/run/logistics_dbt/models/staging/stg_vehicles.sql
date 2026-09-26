
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.stg_vehicles
         as
        (

select
    vehicle_id,
    type,
    capacity_kg
from LOGISTICS_DB.STAGING.stg_dim_vehicle
        );
      
  