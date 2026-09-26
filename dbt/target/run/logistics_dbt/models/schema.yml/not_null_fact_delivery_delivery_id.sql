
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select delivery_id
from LOGISTICS_DB.ANALYTICS.fact_delivery
where delivery_id is null



  
  
      
    ) dbt_internal_test