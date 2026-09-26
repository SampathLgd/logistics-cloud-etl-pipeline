import os
import logging
import argparse
import tempfile
from datetime import datetime

import boto3
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("spark_transform")

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
RAW_ENTITIES = ["drivers", "vehicles", "locations", "deliveries", "delivery_events"]
LATE_THRESHOLD_MINUTES = 15


def download_raw_files(date_str: str, local_dir: str) -> dict:
    s3 = boto3.client("s3", region_name=AWS_REGION)
    local_paths = {}
    for entity in RAW_ENTITIES:
        key = f"raw/{entity}/{date_str}/{entity}.json"
        local_path = os.path.join(local_dir, f"{entity}.json")
        logger.info("Downloading s3://%s/%s", S3_BUCKET, key)
        s3.download_file(S3_BUCKET, key, local_path)
        local_paths[entity] = local_path
    return local_paths


def upload_parquet(local_dir: str, date_str: str, dataset_name: str):
    s3 = boto3.client("s3", region_name=AWS_REGION)
    prefix = f"processed/{dataset_name}/delivery_date={date_str}/"

    # Remove previous output for this exact dataset/date.
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        objects = [
            {"Key": obj["Key"]}
            for obj in page.get("Contents", [])
        ]

        if objects:
            s3.delete_objects(
                Bucket=S3_BUCKET,
                Delete={"Objects": objects}
            )

    uploaded = 0

    for root, _, files in os.walk(local_dir):
        for fname in files:
            if fname.startswith("_") or fname.startswith("."):
                continue

            local_file = os.path.join(root, fname)
            key = f"{prefix}{fname}"

            s3.upload_file(local_file, S3_BUCKET, key)
            uploaded += 1

    logger.info(
        "Uploaded %s file(s) for '%s' to s3://%s/%s",
        uploaded,
        dataset_name,
        S3_BUCKET,
        prefix,
    )
    
def load_entity(spark, path: str):
    envelope_df = spark.read.option("multiLine", True).json(path)
    return envelope_df.select(F.explode("records").alias("r")).select("r.*")


def main():
    parser = argparse.ArgumentParser(description="PySpark transformation for the logistics pipeline.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()
    date_str = args.date

    logger.info("=== Spark transform started for date=%s ===", date_str)
    spark = SparkSession.builder.appName(f"logistics-transform-{date_str}").getOrCreate()

    with tempfile.TemporaryDirectory() as tmp_raw, tempfile.TemporaryDirectory() as tmp_out:
        raw_paths = download_raw_files(date_str, tmp_raw)

        drivers = load_entity(spark, raw_paths["drivers"])
        vehicles = load_entity(spark, raw_paths["vehicles"])
        locations = load_entity(spark, raw_paths["locations"])
        deliveries = load_entity(spark, raw_paths["deliveries"])
        events = load_entity(spark, raw_paths["delivery_events"])

        logger.info(
            "Raw row counts — drivers=%s vehicles=%s locations=%s deliveries=%s events=%s",
            drivers.count(), vehicles.count(), locations.count(), deliveries.count(), events.count(),
        )

        deliveries = (
            deliveries
            .dropDuplicates(["delivery_id"])
            .filter(F.col("delivery_id").isNotNull())
            .withColumn("delivery_status", F.upper(F.trim(F.col("delivery_status"))))
            .withColumn("scheduled_pickup_time", F.to_timestamp("scheduled_pickup_time"))
            .withColumn("actual_pickup_time", F.to_timestamp("actual_pickup_time"))
            .withColumn("scheduled_delivery_time", F.to_timestamp("scheduled_delivery_time"))
            .withColumn("actual_delivery_time", F.to_timestamp("actual_delivery_time"))
            .withColumn("delivery_attempts", F.col("delivery_attempts").cast(IntegerType()))
            .withColumn("distance_km", F.col("distance_km").cast(DoubleType()))
        )

        events = (
            events
            .dropDuplicates(["event_id"])
            .filter(F.col("event_id").isNotNull() & F.col("delivery_id").isNotNull())
            .withColumn("status", F.upper(F.trim(F.col("status"))))
            .withColumn("event_timestamp", F.to_timestamp("event_timestamp"))
        )

        deliveries_clean = (
            deliveries
            .join(drivers.select("driver_id"), "driver_id", "left_semi")
            .join(vehicles.select("vehicle_id"), "vehicle_id", "left_semi")
            .join(
                locations.select(F.col("location_id").alias("pickup_location_id")),
                "pickup_location_id", "left_semi",
            )
            .join(
                locations.select(F.col("location_id").alias("delivery_location_id")),
                "delivery_location_id", "left_semi",
            )
        )

        dropped = deliveries.count() - deliveries_clean.count()
        if dropped > 0:
            logger.warning("Dropped %s deliveries with invalid driver/vehicle/location references", dropped)

        fact_delivery = (
            deliveries_clean
            .withColumn(
                "delivery_duration_minutes",
                (F.col("actual_delivery_time").cast("long") - F.col("actual_pickup_time").cast("long")) / 60.0,
            )
            .withColumn(
                "delay_minutes",
                (F.col("actual_delivery_time").cast("long") - F.col("scheduled_delivery_time").cast("long")) / 60.0,
            )
            .withColumn(
                "is_late",
                F.when(F.col("delay_minutes") > LATE_THRESHOLD_MINUTES, True).otherwise(False),
            )
            .withColumn(
                "distance_bucket",
                F.when(F.col("distance_km") < 10, "0-10km")
                 .when(F.col("distance_km") < 25, "10-25km")
                 .when(F.col("distance_km") < 50, "25-50km")
                 .otherwise("50km+"),
            )
            .withColumn("delivery_hour", F.hour("scheduled_pickup_time"))
            .withColumn("delivery_day", F.to_date("scheduled_pickup_time"))
            .withColumn("delivery_week", F.weekofyear("scheduled_pickup_time"))
        )

        fact_delivery_event = events.join(deliveries_clean.select("delivery_id"), "delivery_id", "left_semi")

        logger.info(
            "Processed row counts — fact_delivery=%s fact_delivery_event=%s",
            fact_delivery.count(), fact_delivery_event.count(),
        )

        datasets = {
            "fact_delivery": fact_delivery,
            "fact_delivery_event": fact_delivery_event,
            "dim_driver": drivers,
            "dim_vehicle": vehicles,
            "dim_location": locations,
        }

        for name, df in datasets.items():
            local_path = os.path.join(tmp_out, name)
            df.coalesce(1).write.mode("overwrite").parquet(local_path)
            upload_parquet(local_path, date_str, name)

    spark.stop()
    logger.info("=== Spark transform completed successfully for date=%s ===", date_str)


if __name__ == "__main__":
    main()
