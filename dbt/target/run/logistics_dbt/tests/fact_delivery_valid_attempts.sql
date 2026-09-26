
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from LOGISTICS_DB.ANALYTICS.fact_delivery
where delivery_attempts < 1
  
  
      
    ) dbt_internal_test