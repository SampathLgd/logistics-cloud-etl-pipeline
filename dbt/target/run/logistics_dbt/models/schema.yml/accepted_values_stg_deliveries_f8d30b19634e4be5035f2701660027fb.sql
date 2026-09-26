
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        delivery_status as value_field,
        count(*) as n_records

    from LOGISTICS_DB.ANALYTICS.stg_deliveries
    group by delivery_status

)

select *
from all_values
where value_field not in (
    'ASSIGNED','PICKED_UP','IN_TRANSIT','OUT_FOR_DELIVERY','DELIVERED','FAILED','CANCELLED','RETURNED'
)



  
  
      
    ) dbt_internal_test