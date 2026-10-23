"""Airflow DAG for bounded ONS incremental collection."""

from solarops_factory import make_ons_dag

dag = make_ons_dag()
