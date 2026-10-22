"""Airflow DAG for committed quality verification."""

from solarops_factory import make_dag

dag = make_dag("solarops_quality_daily", None, "quality")
