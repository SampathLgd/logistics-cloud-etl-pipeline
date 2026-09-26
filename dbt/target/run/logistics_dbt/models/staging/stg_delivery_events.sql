
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.stg_delivery_events
         as
        (

select
    event_id,
    delivery_id,
    event_timestamp,
    event_type,
    location_id,
    status
from LOGISTICS_DB.STAGING.stg_fact_delivery_event
        );
      
  