# Manual Testing Guide — Phases 1 to 4

Run these against your OWN AWS account, Snowflake account, and local machine.
The automated smoke test (`tests/test_pipeline_smoke.py`) already proved the
code logic works against a mocked S3 — this guide proves your real
infrastructure is wired correctly.

## Phase 1 — Environment

1. `docker compose ps` → `postgres`, `airflow-webserver`, `airflow-scheduler` all `Up`.
2. Open `http://localhost:8080`, log in `admin`/`admin` → Airflow UI loads (no DAGs yet, expected).
3. AWS console → S3 → your bucket exists and is empty.
4. Snowflake worksheet → `SELECT CURRENT_VERSION();` → returns a version string.

If any of these fail, stop here — nothing downstream will work until this passes.

## Phase 2 — Mock API + Extraction

1. Start the mock API:
   ```
   uvicorn src.mock_api.main:app --reload --port 8000
   ```
2. In a browser or with curl, check:
   ```
   curl http://localhost:8000/health
   ```
   Expect: `{"status":"ok"}`
3. Check pagination:
   ```
   curl "http://localhost:8000/deliveries?date=2026-09-19&page=1&page_size=10"
   ```
   Expect: JSON with `items` (10 records), `page`, `total_pages`.
4. Run the extractor:
   ```
   python -m src.extract.extract_logistics --date 2026-09-19
   ```
   Expect: console ends with `=== Extraction run completed successfully ===`.
5. In the AWS S3 console, browse to your bucket → confirm these exist:
   ```
   raw/drivers/2026-09-19/drivers.json
   raw/vehicles/2026-09-19/vehicles.json
   raw/locations/2026-09-19/locations.json
   raw/deliveries/2026-09-19/deliveries.json
   raw/delivery_events/2026-09-19/delivery_events.json
   ```
6. Open `raw/deliveries/2026-09-19/deliveries.json` in the S3 console (or download it) →
   confirm it has `entity`, `extraction_date`, `ingestion_timestamp`, `record_count`, `records`.
7. **Determinism check**: re-run step 4 for the same date. Compare `record_count`
   logged both times — they must match exactly.
8. **Failure-handling check**: temporarily set a higher failure rate before
   starting the API (`MOCK_API_FAILURE_RATE=0.5 uvicorn src.mock_api.main:app --port 8000`),
   re-run the extractor, and confirm you see retry log lines
   (`Request failed ... attempt 2/3`) and that it still succeeds or fails cleanly
   after 3 attempts. Set it back to the default afterward.

## Phase 3 — PySpark Transform

1. Run:
   ```
   python -m src.transform.spark_transform --date 2026-09-19
   ```
2. Expect log lines: raw row counts, then `Processed row counts — fact_delivery=200 fact_delivery_event=1000`
   (counts will vary if you changed `count` in `data_store.py`).
3. In S3, confirm:
   ```
   processed/fact_delivery/delivery_date=2026-09-19/
   processed/fact_delivery_event/delivery_date=2026-09-19/
   processed/dim_driver/delivery_date=2026-09-19/
   processed/dim_vehicle/delivery_date=2026-09-19/
   processed/dim_location/delivery_date=2026-09-19/
   ```
   each containing a `.parquet` file.
4. Download one Parquet file and inspect it locally:
   ```python
   import pandas as pd
   df = pd.read_parquet("fact_delivery/part-00000-xxxx.parquet")
   print(df.shape)
   print(df[["delivery_id", "delivery_status", "delay_minutes", "is_late"]].head(10))
   assert df["delivery_id"].is_unique
   assert ((df["is_late"]) == (df["delay_minutes"] > 15)).all()
   ```
   Both `assert` lines should run without error.
5. **Rerun-safety check**: run the same command again for the same date.
   Row counts in the logs should be identical, and the S3 objects should be
   overwritten (same file count, not doubled).

## Phase 4 — Snowflake Load

1. In a Snowflake worksheet, run `sql/warehouse_setup.sql` after replacing the
   `<your-bucket-name>`, `<your-aws-key-id>`, `<your-aws-secret-key>` placeholders.
2. Sanity-check the stage can see your files:
   ```sql
   LIST @LOGISTICS_DB.STAGING.LOGISTICS_S3_STAGE/fact_delivery/delivery_date=2026-09-19/;
   ```
   Expect: one `.parquet` file listed. If this returns nothing, the stage
   URL/credentials/region are misconfigured — fix this before running the loader.
3. Run the loader:
   ```
   python -m src.load.load_snowflake --date 2026-09-19
   ```
   Expect: `=== Snowflake load completed successfully ===`.
4. In Snowflake:
   ```sql
   SELECT COUNT(*) FROM LOGISTICS_DB.STAGING.STG_FACT_DELIVERY;
   SELECT COUNT(*) FROM LOGISTICS_DB.STAGING.STG_FACT_DELIVERY_EVENT;
   ```
   Row counts should match what Phase 3 logged.
5. **Idempotency check** (the important one): run step 3 again for the *same*
   date, then re-run the `COUNT(*)` queries. Counts must be unchanged — if
   they doubled, the `MERGE` upsert isn't working as intended.
6. Run `sql/sample_queries.sql` → confirm the late-delivery rate and
   avg-duration-by-distance-bucket numbers look sane (e.g. late rate somewhere
   in a plausible single-digit-to-teens percentage, not 0% or 100%).

## If something fails

Work backward: Phase 4 failure → check Phase 3's S3 output exists → check
Phase 2's raw S3 output exists → check Phase 1's bucket/credentials are
correct. Each phase's output is the next phase's input, so the earliest
broken link is almost always the real problem.
