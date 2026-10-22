"""Airflow DAG for historical ingestion."""

from solarops_factory import make_dag

dag = make_dag("solarops_ingest_daily", "0 2 * * *", "ingest")
