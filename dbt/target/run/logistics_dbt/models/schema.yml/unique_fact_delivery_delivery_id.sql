
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    delivery_id as unique_field,
    count(*) as n_records

from LOGISTICS_DB.ANALYTICS.fact_delivery
where delivery_id is not null
group by delivery_id
having count(*) > 1



  
  
      
    ) dbt_internal_test