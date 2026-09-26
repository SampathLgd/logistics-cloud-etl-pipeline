"""
End-to-end smoke test for Phases 2-4, run against a MOCKED S3 (moto) so it
needs no real AWS credentials. It does NOT touch a real Snowflake account —
the Snowflake loader's SQL-generation logic is unit-tested separately.

Run with: python tests/test_pipeline_smoke.py
"""
import os
import sys
import time
import socket
import subprocess
import importlib

TEST_DATE = "2026-09-19"
TEST_BUCKET = "test-logistics-bucket"
API_PORT = 8001

# --- environment must be set BEFORE importing our modules (they read env at import time) ---
os.environ["MOCK_API_BASE_URL"] = f"http://127.0.0.1:{API_PORT}"
os.environ["S3_BUCKET_NAME"] = TEST_BUCKET
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["MOCK_API_FAILURE_RATE"] = "0"  # deterministic for the smoke test

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moto import mock_aws
import boto3

PASS, FAIL = [], []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {detail}")


def wait_for_api(port, timeout=30):
    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)

    return False


def main():
    print("\n=== 1. Mock API unit checks (FastAPI TestClient) ===")
    from fastapi.testclient import TestClient
    from src.mock_api.main import app
    from src.mock_api import data_store

    client = TestClient(app)
    r = client.get("/health")
    check("mock API /health returns 200", r.status_code == 200, r.text)

    r1 = client.get(f"/deliveries?date={TEST_DATE}&page=1&page_size=50")
    r2 = client.get(f"/deliveries?date={TEST_DATE}&page=1&page_size=50")
    check("deliveries endpoint returns 200", r1.status_code == 200)
    check(
        "same date produces identical deliveries (determinism)",
        r1.json()["items"] == r2.json()["items"],
    )
    total_pages = r1.json()["total_pages"]
    check("pagination metadata present", total_pages >= 1)

    print("\n=== 2. Starting mock API as a real HTTP server (subprocess) ===")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    api_env = os.environ.copy()
    api_env["PYTHONUNBUFFERED"] = "1"

    api_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.mock_api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(API_PORT),
        ],
        cwd=repo_root,
        env=api_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    api_up = wait_for_api(API_PORT)

    if not api_up:
        print(f"  API subprocess return code: {api_proc.poll()}")

        if api_proc.poll() is not None:
            stdout, stderr = api_proc.communicate()
            print("  API subprocess STDOUT:")
            print(stdout)

            print("  API subprocess STDERR:")
            print(stderr)
        else:
            print("  API subprocess is still running but port 8001 is not reachable.")

    check("mock API subprocess reachable on port", api_up)

    try:
        with mock_aws():
            s3 = boto3.client("s3", region_name="us-east-1")
            s3.create_bucket(Bucket=TEST_BUCKET)

            print("\n=== 3. Extraction (Phase 2) against mocked S3 ===")
            import src.extract.extract_logistics as extract_mod
            importlib.reload(extract_mod)  # pick up the env vars set above

            for entity in extract_mod.ENTITY_ENDPOINTS:
                key, count = extract_mod.extract_entity(entity, TEST_DATE)
                check(f"extracted '{entity}' -> {key} ({count} records)", count > 0 or entity in extract_mod.DATE_INDEPENDENT_ENTITIES)

            objects = s3.list_objects_v2(Bucket=TEST_BUCKET, Prefix="raw/")
            raw_keys = [o["Key"] for o in objects.get("Contents", [])]
            check("5 raw files landed in mocked S3", len(raw_keys) == 5, raw_keys)

            # idempotency check: re-extract deliveries, confirm identical record_count
            _, count_a = extract_mod.extract_entity("deliveries", TEST_DATE)
            _, count_b = extract_mod.extract_entity("deliveries", TEST_DATE)
            check("re-extracting same date gives identical record count", count_a == count_b)

            print("\n=== 4. PySpark transform (Phase 3) against mocked S3 ===")
            import src.transform.spark_transform as transform_mod
            importlib.reload(transform_mod)

            sys.argv = ["spark_transform.py", "--date", TEST_DATE]
            transform_mod.main()

            processed_objects = s3.list_objects_v2(Bucket=TEST_BUCKET, Prefix="processed/")
            processed_keys = [o["Key"] for o in processed_objects.get("Contents", [])]
            check("processed Parquet files landed in mocked S3", len(processed_keys) >= 5, processed_keys)

            fact_delivery_keys = [k for k in processed_keys if k.startswith(f"processed/fact_delivery/delivery_date={TEST_DATE}/")]
            check("fact_delivery Parquet partition exists", len(fact_delivery_keys) >= 1)

            # Read one fact_delivery parquet file back and validate business logic
            import pandas as pd
            local_tmp = "/tmp/verify_fact_delivery.parquet"
            s3.download_file(TEST_BUCKET, fact_delivery_keys[0], local_tmp)
            df = pd.read_parquet(local_tmp)

            check("fact_delivery has no duplicate delivery_id", df["delivery_id"].is_unique)
            check(
                "is_late is only True when delay_minutes > 15",
                bool(((df["is_late"]) == (df["delay_minutes"] > 15)).all()),
            )
            check(
                "delivery_status values are one of the defined lifecycle states",
                set(df["delivery_status"].unique()).issubset(
                    {"ASSIGNED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED", "CANCELLED", "RETURNED"}
                ),
            )
            check("distance_bucket has no nulls", df["distance_bucket"].notnull().all())
            print(f"  (fact_delivery row count: {len(df)})")

    finally:
        api_proc.terminate()
        api_proc.wait(timeout=5)

    print("\n=== 5. Snowflake loader (Phase 4) — SQL generation unit check (no live connection) ===")
    from src.load.load_snowflake import build_merge_sql
    sql = build_merge_sql(
        target_table="STG_FACT_DELIVERY",
        temp_table="TMP_STG_FACT_DELIVERY",
        key_cols=["delivery_id"],
        columns=["delivery_id", "driver_id", "delivery_status"],
    )
    check("MERGE SQL includes ON clause with primary key", "ON target.delivery_id = source.delivery_id" in sql)
    check("MERGE SQL includes WHEN NOT MATCHED INSERT", "WHEN NOT MATCHED THEN INSERT" in sql)
    check("MERGE SQL does not update the primary key column", "driver_id = source.driver_id" in sql and "delivery_id = source.delivery_id" not in sql.split("UPDATE SET")[1].split("WHEN NOT MATCHED")[0])

    print("\n=== SUMMARY ===")
    print(f"PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
    if FAIL:
        print("Failed checks:", FAIL)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
