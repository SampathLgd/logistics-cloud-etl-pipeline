# Cloud ETL Pipeline with Airflow Orchestration

End-to-end logistics/delivery data engineering pipeline using Python, AWS S3, PySpark, Snowflake, dbt, Apache Airflow, Docker, and Git.

## Project objective

Build a realistic, interview-defendable batch ETL pipeline for logistics operations:

- Ingest delivery data from a REST API
- Preserve raw data in Amazon S3
- Validate raw data before transformation
- Transform and enrich data with PySpark
- Store processed Parquet in S3
- Load Snowflake staging tables with idempotent MERGE logic
- Model the warehouse with dbt
- Enforce data quality with dbt tests
- Orchestrate the full workflow with Apache Airflow
- Demonstrate retry/failure handling and rerun safety

This project focuses on delivery operations rather than sales/revenue analysis.

## Architecture

```text
                         ┌──────────────────────┐
                         │   Mock REST API      │
                         │      FastAPI         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Apache Airflow    │
                         │   Daily DAG / Retry  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Python Extraction    │
                         │ Pagination + Retry   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      AWS S3 RAW      │
                         │ JSON by entity/date  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Raw Data Validation  │
                         │ schema/count checks  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      PySpark         │
                         │ transform + enrich   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   AWS S3 PROCESSED   │
                         │      Parquet         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Snowflake       │
                         │       STAGING        │
                         │   MERGE / Upsert     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        dbt           │
                         │ staging / dimensions │
                         │ facts / marts / test │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Snowflake ANALYTICS  │
                         │ daily metrics +      │
                         │ delay summary        │
                         └──────────────────────┘
```

An image version of the architecture is provided separately in the packaging bundle.

## Airflow DAG

DAG ID:

```text
logistics_delivery_pipeline
```

Task dependency:

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

Schedule:

```text
0 2 * * *
```

The DAG uses two retries with a two-minute retry delay.

## Technology stack

| Layer | Technology |
|---|---|
| Source | FastAPI mock REST API |
| Extraction | Python + requests |
| Object storage | Amazon S3 |
| Transformation | PySpark 3.5.1 |
| Warehouse | Snowflake |
| Modeling | dbt + dbt-snowflake |
| Orchestration | Apache Airflow 2.9.3 |
| Containers | Docker Compose |
| Version control | Git / GitHub |

## Data model

### Dimensions

- `DIM_DRIVER`
- `DIM_VEHICLE`
- `DIM_LOCATION`
- `DIM_DATE`

### Facts

- `FACT_DELIVERY`
- `FACT_DELIVERY_EVENT`

### Analytics marts

- `LOGISTICS_DAILY_METRICS`
- `DELIVERY_DELAY_SUMMARY`

## Raw S3 layout

```text
s3://<bucket>/raw/
├── deliveries/YYYY-MM-DD/deliveries.json
├── delivery_events/YYYY-MM-DD/delivery_events.json
├── drivers/YYYY-MM-DD/drivers.json
├── locations/YYYY-MM-DD/locations.json
└── vehicles/YYYY-MM-DD/vehicles.json
```

Raw files use an envelope containing:

- entity
- extraction date
- ingestion timestamp
- record count
- records

## Processed S3 layout

```text
s3://<bucket>/processed/
├── fact_delivery/delivery_date=YYYY-MM-DD/
├── fact_delivery_event/delivery_date=YYYY-MM-DD/
├── dim_driver/delivery_date=YYYY-MM-DD/
├── dim_vehicle/delivery_date=YYYY-MM-DD/
└── dim_location/delivery_date=YYYY-MM-DD/
```

The Spark upload step removes the existing objects for the exact dataset/date prefix before writing fresh output. This prevents duplicate Parquet files when the same date is rerun.

## Data quality

dbt tests cover:

- `not_null`
- `unique`
- `accepted_values`
- `relationships`

Additional singular business-rule tests cover:

- non-negative delivery distance
- valid delivery attempts
- late-flag consistency
- valid mart late-rate values

Validated state as of 2026-09-26:

```text
13 dbt models  → PASS
34 dbt tests   → PASS
WARN           → 0
ERROR          → 0
```

## Failure and retry behavior

A controlled API outage was tested:

```text
Mock API stopped
      ↓
extract_logistics_data
      ↓
up_for_retry
      ↓
Mock API restarted
      ↓
automatic retry
      ↓
success on Try #2
```

The rest of the pipeline then continued successfully.

## Verified pipeline runs

The Airflow environment has successfully run the pipeline for multiple daily execution dates.

Validated warehouse totals:

```text
STG_DIM_DRIVER           20
STG_DIM_VEHICLE          15
STG_DIM_LOCATION         12
STG_FACT_DELIVERY        600
STG_FACT_DELIVERY_EVENT  3000
```

The fact-table totals represent three successful daily loads:

```text
200 deliveries/day × 3 days = 600
1000 events/day × 3 days   = 3000
```

The date distribution was verified for:

```text
2026-09-19
2026-09-25
2026-09-26
```

## Analytics examples

The current generated dataset produces these descriptive daily metrics:

| Date | Deliveries | Delivered | Failed | Late | Late rate |
|---|---:|---:|---:|---:|---:|
| 2026-09-19 | 200 | 173 | 17 | 146 | 73.00% |
| 2026-09-25 | 200 | 173 | 17 | 146 | 73.00% |
| 2026-09-26 | 200 | 173 | 17 | 146 | 73.00% |

The zone-level mart currently contains:

| Zone | Deliveries | Late | Late rate | Avg delay (min) |
|---|---:|---:|---:|---:|
| Zone-A | 87 | 66 | 75.86% | 54.17 |
| Zone-B | 141 | 120 | 85.11% | 45.58 |
| Zone-C | 264 | 171 | 64.77% | 50.34 |
| Zone-D | 108 | 81 | 75.00% | 31.97 |

These values come from controlled synthetic/mock logistics data and are intended for pipeline demonstration and testing.

See `sql/sample_queries.sql` for reusable Snowflake queries.

## Local setup

### 1. Clone

```bash
git clone <your-repository-url>
cd project-3-logistics-data-pipeline
```

### 2. Configure environment

Copy the example file:

```bash
cp .env.example .env
```

Fill in your AWS and Snowflake credentials locally.

Never commit `.env`.

### 3. Start the stack

```bash
docker compose build
docker compose up -d
```

Check services:

```bash
docker compose ps
```

Expected core services:

```text
postgres
airflow-init
airflow-webserver
airflow-scheduler
mock-api
```

### 4. Open Airflow

```text
http://localhost:8080
```

Use the Airflow admin credentials configured in `docker-compose.yml`.

### 5. Run the DAG

Enable:

```text
logistics_delivery_pipeline
```

Then trigger it from the Airflow UI.

## Useful verification commands

List the DAG:

```bash
docker exec project-3-logistics-data-pipeline-airflow-scheduler-1 \
airflow dags list | grep logistics
```

Check import errors:

```bash
docker exec project-3-logistics-data-pipeline-airflow-scheduler-1 \
airflow dags list-import-errors
```

Run dbt tests:

```bash
docker exec project-3-logistics-data-pipeline-airflow-scheduler-1 \
dbt test --project-dir /opt/airflow/dbt
```

Validate raw data:

```bash
docker exec project-3-logistics-data-pipeline-airflow-scheduler-1 \
python /opt/airflow/src/validate/validate_raw.py --date YYYY-MM-DD
```

## Security

- `.env` is local-only and must remain untracked.
- `.env.example` contains placeholders only.
- Rotate credentials immediately if AWS or Snowflake credentials are accidentally exposed.

## Repository structure

```text
project-3-logistics-data-pipeline/
├── airflow/
│   ├── dags/
│   │   └── logistics_pipeline.py
│   └── Dockerfile
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── dimensions/
│   │   ├── facts/
│   │   └── marts/
│   └── tests/
├── docs/
│   ├── architecture.mmd
│   ├── architecture.svg
│   ├── evidence.md
│   └── manual_testing_guide.md
├── sql/
│   ├── warehouse_setup.sql
│   └── sample_queries.sql
├── src/
│   ├── extract/
│   ├── load/
│   ├── mock_api/
│   ├── transform/
│   └── validate/
├── tests/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Interview talking points

Be ready to explain:

1. Why S3 is used for raw and processed layers.
2. Why PySpark is used before warehouse modeling.
3. Why Snowflake is the warehouse.
4. Why dbt is separate from PySpark.
5. Why Airflow is used instead of a simple cron job.
6. How pagination and retries work in the extractor.
7. How reruns avoid duplicate warehouse records.
8. How the raw validator acts as a quality gate.
9. How dbt tests detect data-quality issues.
10. What happens when the upstream API is unavailable.

## Optional future improvements

- Add GitHub Actions for Python/dbt/Docker checks.
- Add CI linting and automated unit tests.
- Add alerting integration for failed DAG runs.
- Add incremental dbt models as the dataset grows.
- Add richer operational dashboards.
