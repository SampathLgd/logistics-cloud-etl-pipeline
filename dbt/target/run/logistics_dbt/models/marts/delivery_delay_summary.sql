
  
    

        create or replace transient table LOGISTICS_DB.ANALYTICS.delivery_delay_summary
         as
        (

select
    l.zone,
    count(*) as total_deliveries,
    count_if(f.is_late) as late_deliveries,
    round(
        100.0 * count_if(f.is_late) / nullif(count(*), 0),
        2
    ) as late_delivery_rate_pct,
    round(avg(f.delay_minutes), 2) as avg_delay_minutes,
    round(avg(f.delivery_duration_minutes), 2) as avg_delivery_duration_minutes,
    round(avg(f.distance_km), 2) as avg_distance_km
from LOGISTICS_DB.ANALYTICS.fact_delivery f
left join LOGISTICS_DB.ANALYTICS.dim_location l
    on f.delivery_location_id = l.location_id
group by l.zone
order by late_delivery_rate_pct desc
        );
      
  