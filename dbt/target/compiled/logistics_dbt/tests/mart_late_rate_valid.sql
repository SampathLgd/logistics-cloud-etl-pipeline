select *
from LOGISTICS_DB.ANALYTICS.logistics_daily_metrics
where late_delivery_rate_pct < 0
   or late_delivery_rate_pct > 100