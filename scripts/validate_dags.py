from airflow.dag_processing.dagbag import DagBag

bag = DagBag("/opt/airflow/dags")
assert not bag.import_errors, bag.import_errors
expected = {
    "solarops_ingest_daily",
    "solarops_quality_daily",
    "solarops_report_monthly",
    "solarops_backfill_manual",
}
assert set(bag.dags) == expected, set(bag.dags)
for dag in bag.dags.values():
    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert all(t.retries == 2 for t in dag.tasks)
print("Validated 4 DAGs; 0 import errors")
