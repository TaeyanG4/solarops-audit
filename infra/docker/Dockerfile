FROM ghcr.io/astral-sh/uv:0.11.29 AS uv
FROM python:3.12.13-slim-bookworm AS worker
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 SOLAROPS_DATA_DIR=/data
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev && useradd --uid 10001 --create-home solarops && mkdir -p /data && chown 10001:10001 /data
USER 10001:10001
ENTRYPOINT ["solarops"]
CMD ["doctor"]

FROM apache/airflow:3.3.2-python3.12 AS airflow
USER airflow
RUN pip install --no-cache-dir apache-airflow==3.3.2 apache-airflow-providers-cncf-kubernetes==10.24.0
COPY --from=worker /opt/venv /opt/venv
COPY --from=worker /app /app
COPY dags /opt/airflow/dags
ENV SOLAROPS_CLI=/opt/venv/bin/solarops PYTHONPATH=/opt/airflow/dags
