
    
    

with child as (
    select delivery_id as from_field
    from LOGISTICS_DB.ANALYTICS.stg_delivery_events
    where delivery_id is not null
),

parent as (
    select delivery_id as to_field
    from LOGISTICS_DB.ANALYTICS.stg_deliveries
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


