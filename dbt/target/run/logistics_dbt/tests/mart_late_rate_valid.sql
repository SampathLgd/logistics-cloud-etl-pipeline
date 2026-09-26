
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from LOGISTICS_DB.ANALYTICS.logistics_daily_metrics
where late_delivery_rate_pct < 0
   or late_delivery_rate_pct > 100
  
  
      
    ) dbt_internal_test