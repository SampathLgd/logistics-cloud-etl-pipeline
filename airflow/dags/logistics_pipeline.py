from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_ROOT = "/opt/airflow"


default_args = {
    "owner": "sampath",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="logistics_delivery_pipeline",
    description="Daily logistics data ETL pipeline",
    start_date=pendulum.datetime(2026, 9, 19, tz="UTC"),
    schedule="0 2 * * *",
    catchup=False,
    default_args=default_args,
    max_active_runs=1,
    tags=["logistics", "etl", "aws", "snowflake", "dbt"],
) as dag:

    extract_logistics_data = BashOperator(
        task_id="extract_logistics_data",
        bash_command=(
            f"python {PROJECT_ROOT}/src/extract/extract_logistics.py "
            '--date "{{ ds }}"'
        ),
    )

    validate_raw_data = BashOperator(
        task_id="validate_raw_data",
        bash_command=(
            f"python {PROJECT_ROOT}/src/validate/validate_raw.py "
            '--date "{{ ds }}"'
        ),
    )

    spark_transform = BashOperator(
        task_id="spark_transform",
        bash_command=(
            f"python {PROJECT_ROOT}/src/transform/spark_transform.py "
            '--date "{{ ds }}"'
        ),
    )

    load_snowflake = BashOperator(
        task_id="load_snowflake",
        bash_command=(
            f"python {PROJECT_ROOT}/src/load/load_snowflake.py "
            '--date "{{ ds }}"'
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "dbt run --project-dir /opt/airflow/dbt"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "dbt test --project-dir /opt/airflow/dbt"
        ),
    )

    (
        extract_logistics_data
        >> validate_raw_data
        >> spark_transform
        >> load_snowflake
        >> dbt_run
        >> dbt_test
    )
