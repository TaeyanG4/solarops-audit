"""Airflow DAG for monthly reports."""

from solarops_factory import make_dag

dag = make_dag("solarops_report_monthly", "0 3 2 * *", "report")
