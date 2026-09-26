import os
import logging
import argparse
from datetime import datetime

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("load_snowflake")

SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "LOGISTICS_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "LOGISTICS_DB"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "STAGING"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
}

# dataset_name (S3 prefix / Phase 3 output) -> (target_table, primary_key_columns)
DATASETS = {
    "dim_driver": ("STG_DIM_DRIVER", ["driver_id"]),
    "dim_vehicle": ("STG_DIM_VEHICLE", ["vehicle_id"]),
    "dim_location": ("STG_DIM_LOCATION", ["location_id"]),
    "fact_delivery": ("STG_FACT_DELIVERY", ["delivery_id"]),
    "fact_delivery_event": ("STG_FACT_DELIVERY_EVENT", ["event_id"]),
}

STAGE_NAME = "LOGISTICS_S3_STAGE"


def get_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)


def build_merge_sql(target_table: str, temp_table: str, key_cols: list, columns: list) -> str:
    on_clause = " AND ".join(f"target.{c} = source.{c}" for c in key_cols)
    update_clause = ", ".join(f"{c} = source.{c}" for c in columns if c not in key_cols)
    insert_cols = ", ".join(columns)
    insert_vals = ", ".join(f"source.{c}" for c in columns)
    return f"""
        MERGE INTO {target_table} AS target
        USING {temp_table} AS source
        ON {on_clause}
        WHEN MATCHED THEN UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
    """


def load_dataset(conn, dataset_name: str, target_table: str, key_cols: list, date_str: str) -> int:
    """Idempotent load: COPY INTO a temp table, then MERGE (upsert) into the
    real staging table on the primary key, so rerunning a date never creates
    duplicate rows. Full idempotency discussion continues in Phase 7."""
    cursor = conn.cursor()
    temp_table = f"TMP_{target_table}"
    stage_path = f"@{STAGE_NAME}/{dataset_name}/delivery_date={date_str}/"

    try:
        logger.info("Loading %s from %s", target_table, stage_path)

        cursor.execute(f"CREATE OR REPLACE TEMPORARY TABLE {temp_table} LIKE {target_table}")

        copy_sql = f"""
            COPY INTO {temp_table}
            FROM {stage_path}
            FILE_FORMAT = (FORMAT_NAME = 'PARQUET_FORMAT')
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        """
        cursor.execute(copy_sql)
        result = cursor.fetchall()
        rows_loaded = sum(row[3] for row in result) if result else 0
        logger.info("Staged %s rows into %s", rows_loaded, temp_table)

        if rows_loaded == 0:
            logger.warning("No rows found in %s for date=%s — skipping merge", dataset_name, date_str)
            return 0

        cursor.execute(f"SELECT * FROM {target_table} LIMIT 0")
        columns = [desc[0] for desc in cursor.description]
        merge_sql = build_merge_sql(target_table, temp_table, key_cols, columns)
        cursor.execute(merge_sql)
        logger.info("Merged %s into %s (upsert on %s)", dataset_name, target_table, key_cols)
        return rows_loaded
    finally:
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.close()


def main():
    parser = argparse.ArgumentParser(description="Load processed Parquet from S3 into Snowflake staging tables.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--datasets", nargs="+", default=list(DATASETS.keys()))
    args = parser.parse_args()

    logger.info("=== Snowflake load started for date=%s ===", args.date)
    conn = get_connection()
    summary = {}

    try:
        for dataset_name in args.datasets:
            target_table, key_cols = DATASETS[dataset_name]
            try:
                rows = load_dataset(conn, dataset_name, target_table, key_cols, args.date)
                summary[dataset_name] = {"status": "success", "rows": rows}
            except Exception as exc:
                logger.exception("Load failed for %s", dataset_name)
                summary[dataset_name] = {"status": "failed", "error": str(exc)}
    finally:
        conn.close()

    logger.info("=== Snowflake load summary ===")
    for name, result in summary.items():
        logger.info("%s: %s", name, result)

    if any(r["status"] == "failed" for r in summary.values()):
        raise SystemExit(1)

    logger.info("=== Snowflake load completed successfully ===")


if __name__ == "__main__":
    main()
