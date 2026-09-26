
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select pickup_location_id as from_field
    from LOGISTICS_DB.ANALYTICS.fact_delivery
    where pickup_location_id is not null
),

parent as (
    select location_id as to_field
    from LOGISTICS_DB.ANALYTICS.dim_location
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test