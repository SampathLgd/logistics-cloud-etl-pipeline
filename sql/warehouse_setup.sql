-- =====================================================================
-- Phase 4: Snowflake warehouse, database, staging schema/tables, stage
-- =====================================================================

-- Warehouse
CREATE WAREHOUSE IF NOT EXISTS LOGISTICS_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

-- Database & schemas
CREATE DATABASE IF NOT EXISTS LOGISTICS_DB;
CREATE SCHEMA IF NOT EXISTS LOGISTICS_DB.STAGING;
CREATE SCHEMA IF NOT EXISTS LOGISTICS_DB.ANALYTICS;   -- populated by dbt in Phase 5

USE WAREHOUSE LOGISTICS_WH;
USE DATABASE LOGISTICS_DB;
USE SCHEMA STAGING;

-- File format matching the Parquet output from PySpark (Phase 3)
CREATE OR REPLACE FILE FORMAT LOGISTICS_DB.STAGING.PARQUET_FORMAT
  TYPE = PARQUET;

-- External stage pointing at the processed zone of the S3 bucket.
--
-- SIMPLIFICATION (call this out explicitly if asked):
-- This uses long-lived AWS keys directly on the stage, which is fine for a
-- portfolio project but NOT what you'd do in production. A production setup
-- uses a Snowflake STORAGE INTEGRATION, which authorizes Snowflake via an
-- IAM role trust relationship instead of embedding static credentials.
CREATE OR REPLACE STAGE LOGISTICS_DB.STAGING.LOGISTICS_S3_STAGE
  URL = 's3://<your-bucket-name>/processed/'
  CREDENTIALS = (AWS_KEY_ID = '<your-aws-key-id>' AWS_SECRET_KEY = '<your-aws-secret-key>')
  FILE_FORMAT = LOGISTICS_DB.STAGING.PARQUET_FORMAT;

-- Staging tables — structure mirrors the Parquet columns PySpark produced.
-- These are loaded by src/load/load_snowflake.py; dbt builds the star
-- schema (dim_*/fact_*) on TOP of these in Phase 5.

CREATE TABLE IF NOT EXISTS LOGISTICS_DB.STAGING.STG_DIM_DRIVER (
    driver_id     STRING,
    name          STRING,
    hire_date     DATE,
    region        STRING
);

CREATE TABLE IF NOT EXISTS LOGISTICS_DB.STAGING.STG_DIM_VEHICLE (
    vehicle_id    STRING,
    type          STRING,
    capacity_kg   NUMBER
);

CREATE TABLE IF NOT EXISTS LOGISTICS_DB.STAGING.STG_DIM_LOCATION (
    location_id   STRING,
    city          STRING,
    zone          STRING,
    latitude      FLOAT,
    longitude     FLOAT
);

CREATE TABLE IF NOT EXISTS LOGISTICS_DB.STAGING.STG_FACT_DELIVERY (
    delivery_id                STRING,
    driver_id                  STRING,
    vehicle_id                 STRING,
    pickup_location_id         STRING,
    delivery_location_id       STRING,
    scheduled_pickup_time      TIMESTAMP_NTZ,
    actual_pickup_time         TIMESTAMP_NTZ,
    scheduled_delivery_time    TIMESTAMP_NTZ,
    actual_delivery_time       TIMESTAMP_NTZ,
    delivery_status            STRING,
    delivery_attempts          NUMBER,
    distance_km                FLOAT,
    delivery_duration_minutes  FLOAT,
    delay_minutes              FLOAT,
    is_late                    BOOLEAN,
    distance_bucket            STRING,
    delivery_hour              NUMBER,
    delivery_day               DATE,
    delivery_week              NUMBER
);

CREATE TABLE IF NOT EXISTS LOGISTICS_DB.STAGING.STG_FACT_DELIVERY_EVENT (
    event_id        STRING,
    delivery_id     STRING,
    event_timestamp TIMESTAMP_NTZ,
    event_type      STRING,
    location_id     STRING,
    status          STRING
);
