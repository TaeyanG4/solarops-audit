"""Airflow DAG for bounded manual replay."""

from solarops_factory import make_dag

dag = make_dag("solarops_backfill_manual", None, "backfill")
