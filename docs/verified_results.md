# Verified Results — 2026-09-26

## Airflow

Three successful DAG runs were present:

- `manual__2026-09-26...`
- `scheduled__2026-09-25...`
- `manual__2026-09-19...`

## Snowflake STAGING

```text
STG_DIM_DRIVER           20
STG_DIM_VEHICLE          15
STG_DIM_LOCATION         12
STG_FACT_DELIVERY        600
STG_FACT_DELIVERY_EVENT  3000
```

Daily distribution:

```text
DELIVERIES
2026-09-19   200
2026-09-25   200
2026-09-26   200

EVENTS
2026-09-19   1000
2026-09-25   1000
2026-09-26   1000
```

## Snowflake ANALYTICS

`LOGISTICS_DAILY_METRICS`:

```text
2026-09-19  200 deliveries  173 delivered  17 failed  146 late  73.00%
2026-09-25  200 deliveries  173 delivered  17 failed  146 late  73.00%
2026-09-26  200 deliveries  173 delivered  17 failed  146 late  73.00%
```

`DELIVERY_DELAY_SUMMARY` contained four zones:

```text
Zone-A  87 deliveries  66 late  75.86% late  54.17 min avg delay
Zone-B 141 deliveries 120 late  85.11% late  45.58 min avg delay
Zone-C 264 deliveries 171 late  64.77% late  50.34 min avg delay
Zone-D 108 deliveries  81 late  75.00% late  31.97 min avg delay
```

## dbt

```text
Models: 13/13 PASS
Tests:  34/34 PASS
WARN:   0
ERROR:  0
```

These results are from controlled synthetic/mock logistics data.
