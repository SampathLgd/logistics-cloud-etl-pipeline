
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from LOGISTICS_DB.ANALYTICS.fact_delivery
where distance_km < 0
  
  
      
    ) dbt_internal_test