"""Run actual scheduled tasks, fault/retry and bounded backfill; retain evidence."""

import argparse
import json
import subprocess
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["compose", "k8s"], default="compose")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
stamp = str(int(time.time()))
if args.mode == "compose":
    prefix = [
        "docker",
        "compose",
        "--env-file",
        str(root / ".env"),
        "-f",
        str(root / "infra/compose/compose.yaml"),
        "exec",
        "-T",
        "airflow-scheduler",
        "airflow",
    ]
else:
    prefix = [
        "kubectl",
        "--kubeconfig",
        str(root / "artifacts/kubeconfig"),
        "-n",
        "solarops",
        "exec",
        "airflow-scheduler-0",
        "-c",
        "scheduler",
        "--",
        "airflow",
    ]


def command(*argv):
    p = subprocess.run(prefix + list(argv), capture_output=True, text=True, check=True)
    return p.stdout


log = root / "artifacts" / f"airflow-{args.mode}-checks.jsonl"
cases = [
    ("solarops_ingest_daily", "normal", {}),
    ("solarops_ingest_daily", "retry", {"fault_marker": "retry-" + stamp}),
    (
        "solarops_backfill_manual",
        "backfill",
        {"from_date": "2024-04-03", "to_date": "2024-04-04", "dry_run": "false"},
    ),
    ("solarops_quality_daily", "quality", {}),
    ("solarops_report_monthly", "report", {}),
]
for dag, scenario, conf in cases:
    run_id = f"{args.mode}-{scenario}-{stamp}"
    command("dags", "unpause", dag)
    command("dags", "trigger", dag, "--run-id", run_id, "--conf", json.dumps(conf))
    print(json.dumps({"started": run_id}), flush=True)
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        runs = json.loads(command("dags", "list-runs", dag, "--output", "json"))
        row = next((r for r in runs if r.get("run_id", r.get("dag_run_id")) == run_id), None)
        if row and row["state"] in ("success", "failed"):
            with log.open("a", encoding="utf-8") as out:
                out.write(json.dumps(dict(scenario=scenario, **row)) + "\n")
            print(json.dumps(row), flush=True)
            if row["state"] != "success":
                raise RuntimeError(f"Failed scenario {run_id}")
            break
        time.sleep(10)
    else:
        raise TimeoutError(run_id)
    command("dags", "pause", dag)
print("Completed normal, injected retry, backfill, quality and report", flush=True)
