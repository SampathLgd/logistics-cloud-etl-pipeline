# Stage 1: get Java 17 without apt
FROM eclipse-temurin:17-jre-jammy AS java

# Stage 2: Airflow
FROM apache/airflow:2.9.3

USER root

# Copy Java 17 runtime
COPY --from=java /opt/java/openjdk /opt/java/openjdk

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Switch back to Airflow's non-root user
USER airflow

# Install additional project dependencies
RUN pip install --no-cache-dir \
    pyspark==3.5.1 \
    dbt-core==1.11.15 \
    dbt-snowflake==1.8.3 \
    boto3==1.34.144 \
    requests==2.32.3 \
    python-dotenv==1.0.1 \
    snowflake-connector-python==3.11.0 \
    pandas \
    pyarrow \
    fastapi==0.111.0 \
    uvicorn==0.30.1 \
    faker==26.0.0