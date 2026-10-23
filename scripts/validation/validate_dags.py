import copy
from datetime import UTC, datetime
from types import SimpleNamespace

from airflow.dag_processing.dagbag import DagBag

bag = DagBag("/opt/airflow/dags")
assert not bag.import_errors, bag.import_errors
expected = {
    "solarops_ingest_daily",
    "solarops_quality_daily",
    "solarops_report_monthly",
    "solarops_backfill_manual",
    "solarops_ons_daily",
    "solarops_public_benchmark_1",
    "solarops_public_benchmark_2",
}
assert set(bag.dags) == expected, set(bag.dags)
for dag in bag.dags.values():
    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert all(t.retries == 2 for t in dag.tasks)
    for kind, plant in (("synthetic", "DEMO_01"), ("public", "PS_001")):
        params = dag.params.validate()
        params.update(source_kind=kind, plant=plant, source_version=f"{kind}-v1")
        for original in dag.tasks:
            task = copy.deepcopy(original)
            task.render_template_fields(
                {
                    "params": params,
                    "dag": dag,
                    "run_id": "validation",
                    "ti": SimpleNamespace(task_id=task.task_id, try_number=1),
                    "data_interval_end": datetime(2026, 10, 23, tzinfo=UTC),
                }
            )
            args = task.arguments if hasattr(task, "arguments") else task.op_args[0]
            if dag.dag_id == "solarops_ons_daily":
                assert args == ["ons-sync", "--as-of", "2026-10-23"], args
                assert dag.max_active_tasks == 1
                continue
            if dag.dag_id.startswith("solarops_public_benchmark_"):
                assert args[args.index("--source-kind") + 1] == "public", args
                assert args[args.index("--plant") + 1] == "PS_001", args
                assert dag.max_active_tasks == int(dag.dag_id[-1])
                continue
            if args[0] == "doctor":
                continue
            assert args[args.index("--plant") + 1] == plant, args
            assert args[args.index("--source-kind") + 1] == kind, args
            if args[0] == "replay":
                assert args[args.index("--source-version") + 1] == f"{kind}-v1", args
                assert args[args.index("--dry-run") + 1] == (
                    "true" if dag.dag_id == "solarops_backfill_manual" else "false"
                ), args
            if dag.dag_id == "solarops_report_monthly":
                assert args[args.index("--period") + 1] == params["period"], args
print("Validated 7 DAGs, ONS schedule and public/synthetic templates; 0 import errors")
