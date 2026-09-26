-- Project 3: Logistics Delivery Data Pipeline
-- Snowflake analytics queries
-- Target schema: LOGISTICS_DB.ANALYTICS
--
-- These queries are designed for portfolio demonstration/interview discussion.
-- They intentionally focus on logistics operations rather than revenue/sales.

USE DATABASE LOGISTICS_DB;
USE SCHEMA ANALYTICS;

-- ============================================================
-- 1. Daily delivery performance
-- ============================================================
SELECT
    DELIVERY_DAY,
    TOTAL_DELIVERIES,
    DELIVERED_DELIVERIES,
    FAILED_DELIVERIES,
    LATE_DELIVERIES,
    LATE_DELIVERY_RATE_PCT,
    AVG_DELIVERY_DURATION_MINUTES,
    AVG_DELAY_MINUTES,
    AVG_DELIVERY_ATTEMPTS,
    AVG_DISTANCE_KM
FROM LOGISTICS_DAILY_METRICS
ORDER BY DELIVERY_DAY;


-- ============================================================
-- 2. Zone-level delay analysis
-- ============================================================
SELECT
    ZONE,
    TOTAL_DELIVERIES,
    LATE_DELIVERIES,
    LATE_DELIVERY_RATE_PCT,
    AVG_DELAY_MINUTES,
    AVG_DELIVERY_DURATION_MINUTES,
    AVG_DISTANCE_KM
FROM DELIVERY_DELAY_SUMMARY
ORDER BY LATE_DELIVERY_RATE_PCT DESC;


-- ============================================================
-- 3. Driver performance
-- Grain: one row per driver
-- ============================================================
SELECT
    d.DRIVER_ID,
    d.NAME,
    d.REGION,
    COUNT(f.DELIVERY_ID) AS TOTAL_DELIVERIES,
    COUNT_IF(f.STATUS = 'DELIVERED') AS DELIVERED_DELIVERIES,
    COUNT_IF(f.STATUS = 'FAILED') AS FAILED_DELIVERIES,
    COUNT_IF(f.IS_LATE) AS LATE_DELIVERIES,
    ROUND(100.0 * COUNT_IF(f.IS_LATE) / NULLIF(COUNT(f.DELIVERY_ID), 0), 2)
        AS LATE_RATE_PCT,
    ROUND(AVG(f.ATTEMPTS), 2) AS AVG_ATTEMPTS,
    ROUND(AVG(f.DISTANCE_KM), 2) AS AVG_DISTANCE_KM
FROM FACT_DELIVERY f
JOIN DIM_DRIVER d
    ON f.DRIVER_ID = d.DRIVER_ID
GROUP BY
    d.DRIVER_ID,
    d.NAME,
    d.REGION
ORDER BY TOTAL_DELIVERIES DESC, LATE_RATE_PCT DESC;


-- ============================================================
-- 4. Vehicle workload and reliability
-- ============================================================
SELECT
    v.VEHICLE_ID,
    v.TYPE,
    v.CAPACITY_KG,
    COUNT(f.DELIVERY_ID) AS TOTAL_DELIVERIES,
    ROUND(SUM(f.DISTANCE_KM), 2) AS TOTAL_DISTANCE_KM,
    ROUND(AVG(f.DISTANCE_KM), 2) AS AVG_DISTANCE_KM,
    ROUND(AVG(f.ATTEMPTS), 2) AS AVG_ATTEMPTS,
    COUNT_IF(f.IS_LATE) AS LATE_DELIVERIES,
    ROUND(100.0 * COUNT_IF(f.IS_LATE) / NULLIF(COUNT(f.DELIVERY_ID), 0), 2)
        AS LATE_RATE_PCT
FROM FACT_DELIVERY f
JOIN DIM_VEHICLE v
    ON f.VEHICLE_ID = v.VEHICLE_ID
GROUP BY
    v.VEHICLE_ID,
    v.TYPE,
    v.CAPACITY_KG
ORDER BY TOTAL_DELIVERIES DESC;


-- ============================================================
-- 5. Failed delivery investigation
-- ============================================================
SELECT
    f.DELIVERY_ID,
    f.DRIVER_ID,
    f.VEHICLE_ID,
    pickup.CITY AS PICKUP_CITY,
    pickup.ZONE AS PICKUP_ZONE,
    dropoff.CITY AS DELIVERY_CITY,
    dropoff.ZONE AS DELIVERY_ZONE,
    f.ATTEMPTS,
    f.DISTANCE_KM,
    f.DELAY_MINUTES,
    f.STATUS
FROM FACT_DELIVERY f
LEFT JOIN DIM_LOCATION pickup
    ON f.PICKUP_LOCATION_ID = pickup.LOCATION_ID
LEFT JOIN DIM_LOCATION dropoff
    ON f.DELIVERY_LOCATION_ID = dropoff.LOCATION_ID
WHERE f.STATUS = 'FAILED'
ORDER BY f.ATTEMPTS DESC, f.DELAY_MINUTES DESC, f.DISTANCE_KM DESC;


-- ============================================================
-- 6. Late-delivery trend by day
-- ============================================================
SELECT
    DELIVERY_DAY,
    TOTAL_DELIVERIES,
    LATE_DELIVERIES,
    LATE_DELIVERY_RATE_PCT,
    AVG_DELAY_MINUTES
FROM LOGISTICS_DAILY_METRICS
ORDER BY DELIVERY_DAY;


-- ============================================================
-- 7. Distance bucket vs delivery performance
-- ============================================================
SELECT
    DISTANCE_BUCKET,
    COUNT(*) AS TOTAL_DELIVERIES,
    ROUND(AVG(DURATION_MINUTES), 2) AS AVG_DURATION_MINUTES,
    ROUND(AVG(DELAY_MINUTES), 2) AS AVG_DELAY_MINUTES,
    ROUND(100.0 * COUNT_IF(IS_LATE) / NULLIF(COUNT(*), 0), 2)
        AS LATE_RATE_PCT
FROM FACT_DELIVERY
GROUP BY DISTANCE_BUCKET
ORDER BY
    CASE DISTANCE_BUCKET
        WHEN '0-10 km' THEN 1
        WHEN '10-25 km' THEN 2
        WHEN '25-50 km' THEN 3
        WHEN '50+ km' THEN 4
        ELSE 99
    END;


-- ============================================================
-- 8. Delivery events by event type
-- ============================================================
SELECT
    EVENT_TYPE,
    STATUS,
    COUNT(*) AS EVENT_COUNT
FROM FACT_DELIVERY_EVENT
GROUP BY EVENT_TYPE, STATUS
ORDER BY EVENT_COUNT DESC, EVENT_TYPE;


-- ============================================================
-- 9. Peak delivery hours
-- ============================================================
SELECT
    DELIVERY_HOUR,
    COUNT(*) AS TOTAL_DELIVERIES,
    ROUND(AVG(DURATION_MINUTES), 2) AS AVG_DURATION_MINUTES,
    ROUND(AVG(DELAY_MINUTES), 2) AS AVG_DELAY_MINUTES,
    ROUND(100.0 * COUNT_IF(IS_LATE) / NULLIF(COUNT(*), 0), 2)
        AS LATE_RATE_PCT
FROM FACT_DELIVERY
GROUP BY DELIVERY_HOUR
ORDER BY DELIVERY_HOUR;


-- ============================================================
-- 10. Duplicate-key check for idempotency verification
-- ============================================================
SELECT
    DELIVERY_ID,
    COUNT(*) AS ROW_COUNT
FROM FACT_DELIVERY
GROUP BY DELIVERY_ID
HAVING COUNT(*) > 1
ORDER BY ROW_COUNT DESC, DELIVERY_ID;

-- Expected result: zero rows.
