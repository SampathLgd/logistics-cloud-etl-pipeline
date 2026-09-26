import argparse
import json
import os
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError


EXPECTED_DATASETS = [
    "deliveries",
    "delivery_events",
    "drivers",
    "locations",
    "vehicles",
]


def validate_raw_data(date: str) -> None:
    bucket = os.environ["S3_BUCKET_NAME"]
    region = os.getenv("AWS_REGION", "ap-south-1")

    s3 = boto3.client("s3", region_name=region)

    print(f"Validating raw S3 data for date: {date}")
    print(f"Bucket: {bucket}")

    total_records = 0

    for dataset in EXPECTED_DATASETS:
        key = f"raw/{dataset}/{date}/{dataset}.json"

        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            payload = json.loads(response["Body"].read())

            if not isinstance(payload, dict):
                raise ValueError("Top-level JSON must be an object")

            if payload.get("entity") != dataset:
                raise ValueError(
                    f"entity mismatch: expected '{dataset}', "
                    f"got '{payload.get('entity')}'"
                )

            if payload.get("extraction_date") != date:
                raise ValueError(
                    f"extraction_date mismatch: expected '{date}', "
                    f"got '{payload.get('extraction_date')}'"
                )

            records = payload.get("records")

            if not isinstance(records, list):
                raise ValueError("missing or invalid 'records' list")

            actual_count = len(records)
            declared_count = payload.get("record_count")

            if actual_count == 0:
                raise ValueError("dataset contains zero records")

            if declared_count != actual_count:
                raise ValueError(
                    f"record_count mismatch: declared={declared_count}, "
                    f"actual={actual_count}"
                )

            print(f"  PASS: {key} -> {actual_count} records")
            total_records += actual_count

        except (
            ClientError,
            BotoCoreError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            print(f"  FAIL: {key} -> {exc}")
            raise

    print(f"Raw validation passed. Total records: {total_records}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate raw logistics data in S3."
    )
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    try:
        validate_raw_data(args.date)
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()