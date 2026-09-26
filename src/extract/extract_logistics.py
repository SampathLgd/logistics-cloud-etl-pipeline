import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("extract_logistics")

API_BASE_URL = os.getenv("MOCK_API_BASE_URL", "http://localhost:8000")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2
PAGE_SIZE = 100

DATE_INDEPENDENT_ENTITIES = {"drivers", "vehicles", "locations"}
ENTITY_ENDPOINTS = {
    "drivers": "/drivers",
    "vehicles": "/vehicles",
    "locations": "/locations",
    "deliveries": "/deliveries",
    "delivery_events": "/delivery_events",
}


def fetch_all_pages(endpoint: str, params: dict) -> list:
    all_items = []
    page = 1

    while True:
        query = {**params, "page": page, "page_size": PAGE_SIZE}
        attempt = 0
        while True:
            attempt += 1
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", params=query, timeout=10)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as exc:
                logger.warning("Request failed (%s) for %s page %s, attempt %s/%s", exc, endpoint, page, attempt, MAX_RETRIES)
                if attempt >= MAX_RETRIES:
                    logger.error("Giving up on %s page %s after %s attempts", endpoint, page, MAX_RETRIES)
                    raise
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        payload = response.json()
        if "items" not in payload or "total_pages" not in payload:
            raise ValueError(f"Unexpected response structure from {endpoint}: {list(payload.keys())}")

        all_items.extend(payload["items"])
        logger.info("Fetched %s page %s/%s (%s items so far)", endpoint, page, payload["total_pages"], len(all_items))

        if page >= payload["total_pages"]:
            break
        page += 1

    return all_items


def save_raw_to_s3(entity: str, date_str: str, records: list) -> str:
    if not S3_BUCKET:
        raise EnvironmentError("S3_BUCKET_NAME is not set in the environment")

    envelope = {
        "entity": entity,
        "extraction_date": date_str,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "records": records,
    }

    s3_key = f"raw/{entity}/{date_str}/{entity}.json"
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(envelope, default=str).encode("utf-8"),
        ContentType="application/json",
    )

    logger.info("Uploaded %s records for '%s' to s3://%s/%s", len(records), entity, S3_BUCKET, s3_key)
    return s3_key


def extract_entity(entity: str, date_str: str):
    endpoint = ENTITY_ENDPOINTS[entity]
    params = {} if entity in DATE_INDEPENDENT_ENTITIES else {"date": date_str}

    logger.info("Starting extraction for '%s' (date=%s)", entity, date_str)
    records = fetch_all_pages(endpoint, params)

    if not records:
        logger.warning("No records returned for '%s' on %s", entity, date_str)

    return save_raw_to_s3(entity, date_str, records), len(records)


def main():
    parser = argparse.ArgumentParser(description="Extract logistics data from the mock API into raw S3.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--entities", nargs="+", default=list(ENTITY_ENDPOINTS.keys()))
    args = parser.parse_args()

    logger.info("=== Extraction run started for date=%s ===", args.date)
    summary, failures = {}, []

    for entity in args.entities:
        try:
            s3_key, count = extract_entity(entity, args.date)
            summary[entity] = {"status": "success", "s3_key": s3_key, "record_count": count}
        except Exception as exc:
            logger.exception("Extraction failed for entity '%s'", entity)
            summary[entity] = {"status": "failed", "error": str(exc)}
            failures.append(entity)

    logger.info("=== Extraction run summary ===")
    for entity, result in summary.items():
        logger.info("%s: %s", entity, result)

    if failures:
        logger.error("Extraction run completed with failures: %s", failures)
        sys.exit(1)

    logger.info("=== Extraction run completed successfully ===")


if __name__ == "__main__":
    main()
