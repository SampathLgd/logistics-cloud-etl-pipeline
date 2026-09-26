
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select delivery_status
from LOGISTICS_DB.ANALYTICS.stg_deliveries
where delivery_status is null



  
  
      
    ) dbt_internal_test