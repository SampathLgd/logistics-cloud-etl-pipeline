
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.dim_vehicle
         as
        (

select
    vehicle_id,
    type as vehicle_type,
    capacity_kg
from LOGISTICS_DB.ANALYTICS.stg_vehicles
        );
      
  