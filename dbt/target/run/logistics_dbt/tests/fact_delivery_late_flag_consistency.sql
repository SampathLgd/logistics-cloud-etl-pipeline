
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from LOGISTICS_DB.ANALYTICS.fact_delivery
where actual_delivery_time is not null
  and is_late != (delay_minutes > 15)
  
  
      
    ) dbt_internal_test