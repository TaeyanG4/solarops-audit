FROM ghcr.io/astral-sh/uv:0.11.29@sha256:eb2843a1e56fd9e30c7276ce1a52cba86e64c7b385f5e3279a0e08e02dd058fc AS uv
FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2 AS worker
ARG SOURCE_REVISION=unrecorded
LABEL org.opencontainers.image.revision=$SOURCE_REVISION
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 SOLAROPS_DATA_DIR=/data
ENV SOLAROPS_BUILD_REVISION=$SOURCE_REVISION SOLAROPS_DUCKDB_TEMP_DIR=/tmp/solarops-duckdb
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev && useradd --uid 10001 --create-home solarops && mkdir -p /data && chown 10001:10001 /data
USER 10001:10001
ENTRYPOINT ["solarops"]
CMD ["doctor"]

FROM apache/airflow:3.3.2-python3.12@sha256:9df9c8be4096b9cc626bd7cb1f2b8c712eef66c59c615f8c7e6200871ca10bd1 AS airflow
ARG SOURCE_REVISION=unrecorded
LABEL org.opencontainers.image.revision=$SOURCE_REVISION
USER airflow
COPY infra/docker/airflow-constraints-3.12.txt /opt/airflow/constraints.txt
RUN pip install --no-cache-dir --constraint /opt/airflow/constraints.txt apache-airflow==3.3.2 apache-airflow-providers-cncf-kubernetes==10.24.0 && pip check
COPY --from=worker /opt/venv /opt/venv
COPY --from=worker /app /app
COPY dags /opt/airflow/dags
ENV SOLAROPS_CLI=/opt/venv/bin/solarops PYTHONPATH=/opt/airflow/dags
ENV SOLAROPS_BUILD_REVISION=$SOURCE_REVISION SOLAROPS_RELEASE_FILE=/app/src/solarops/release.json SOLAROPS_DUCKDB_TEMP_DIR=/tmp/solarops-duckdb
