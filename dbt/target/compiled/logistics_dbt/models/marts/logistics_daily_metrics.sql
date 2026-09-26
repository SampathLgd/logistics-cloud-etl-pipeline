

select
    delivery_day,
    count(*) as total_deliveries,
    count_if(delivery_status = 'DELIVERED') as delivered_deliveries,
    count_if(delivery_status = 'FAILED') as failed_deliveries,
    count_if(is_late) as late_deliveries,
    round(100.0 * count_if(is_late) / nullif(count(*), 0), 2) as late_delivery_rate_pct,
    round(avg(delivery_duration_minutes), 2) as avg_delivery_duration_minutes,
    round(avg(delay_minutes), 2) as avg_delay_minutes,
    round(avg(delivery_attempts), 2) as avg_delivery_attempts,
    round(avg(distance_km), 2) as avg_distance_km
from LOGISTICS_DB.ANALYTICS.fact_delivery
group by delivery_day
order by delivery_day