
    
    

select
    event_id as unique_field,
    count(*) as n_records

from LOGISTICS_DB.ANALYTICS.fact_delivery_event
where event_id is not null
group by event_id
having count(*) > 1


