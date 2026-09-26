
    
    

select
    vehicle_id as unique_field,
    count(*) as n_records

from LOGISTICS_DB.ANALYTICS.dim_vehicle
where vehicle_id is not null
group by vehicle_id
having count(*) > 1


