# Project Evidence

The following evidence was captured during end-to-end validation.

## 1. Airflow successful DAG run

Shows the DAG enabled with all six tasks green after a successful manual run.

Suggested screenshot filename:

```text
airflow-success.png
```

## 2. Airflow Graph view

Shows the dependency chain:

```text
extract_logistics_data
        ↓
validate_raw_data
        ↓
spark_transform
        ↓
load_snowflake
        ↓
dbt_run
        ↓
dbt_test
```

Suggested screenshot filename:

```text
airflow-graph.png
```

## 3. Airflow retry demonstration

The Mock API was intentionally stopped. `extract_logistics_data` entered:

```text
up_for_retry
```

on Try #1.

Suggested screenshot filename:

```text
airflow-up-for-retry.png
```

## 4. Successful automatic retry

After restarting the Mock API, the same task succeeded on Try #2.

Suggested screenshot filename:

```text
airflow-retry-success.png
```

## 5. dbt validation

The complete pipeline executed:

```text
13 models → PASS=13
34 tests  → PASS=34
WARN      → 0
ERROR     → 0
```

Keep the terminal/DAG log capture for this as supporting evidence.

## 6. Snowflake analytics

Validated analytics outputs included:

- `LOGISTICS_DAILY_METRICS`: 3 daily rows
- `DELIVERY_DELAY_SUMMARY`: 4 zone rows
- Three daily loads represented 600 fact deliveries and 3,000 delivery events in STAGING.

## Recommended evidence folder

```text
docs/evidence/
├── airflow-success.png
├── airflow-graph.png
├── airflow-up-for-retry.png
└── airflow-retry-success.png
```
