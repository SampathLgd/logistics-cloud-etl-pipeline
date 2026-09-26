
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select delivery_id
from LOGISTICS_DB.ANALYTICS.stg_deliveries
where delivery_id is null



  
  
      
    ) dbt_internal_test