

with bounds as (
    select
        min(delivery_day) as min_date,
        max(delivery_day) as max_date
    from LOGISTICS_DB.ANALYTICS.stg_deliveries
),

date_series as (
    select
        dateadd(day, seq4(), min_date)::date as date_day,
        max_date
    from bounds,
         table(generator(rowcount => 365))
)

select
    date_day,
    year(date_day) as year,
    month(date_day) as month,
    day(date_day) as day,
    dayofweekiso(date_day) as day_of_week,
    weekofyear(date_day) as week_of_year,
    dayofyear(date_day) as day_of_year,
    case
        when dayofweekiso(date_day) between 1 and 5 then true
        else false
    end as is_weekday
from date_series
where date_day <= max_date