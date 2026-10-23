"""Run actual scheduled tasks, fault/retry and bounded backfill; retain evidence."""

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["compose", "k8s"], default="compose")
parser.add_argument("--source-kind", choices=["synthetic", "public"], default="synthetic")
parser.add_argument("--plant")
parser.add_argument("--from", dest="start")
parser.add_argument("--to", dest="end")
parser.add_argument("--source-version")
parser.add_argument("--period")
parser.add_argument(
    "--ons", action="store_true", help="Run only the real ONS incremental collection DAG"
)
args = parser.parse_args()
if args.source_kind == "public" and not all(
    (args.plant, args.start, args.end, args.source_version, args.period)
):
    parser.error("Public checks require --plant, --from, --to, --source-version and --period")
root = Path(__file__).resolve().parents[2]
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


kind = "ons" if args.ons else args.source_kind
log = root / "artifacts" / f"airflow-{args.mode}-{kind}-checks.jsonl"
log.parent.mkdir(parents=True, exist_ok=True)
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
if args.source_kind == "public":
    common = {
        "source_kind": "public",
        "plant": args.plant,
        "from_date": args.start,
        "to_date": args.end,
        "source_version": args.source_version,
        "period": args.period,
    }
    cases = [
        ("solarops_backfill_manual", "plan", dict(common, dry_run="true")),
        ("solarops_ingest_daily", "normal", dict(common, dry_run="false")),
        ("solarops_backfill_manual", "backfill", dict(common, dry_run="false")),
        ("solarops_quality_daily", "quality", common),
        ("solarops_report_monthly", "report", common),
    ]
if args.ons:
    # Real public network collection: previous and current month as of today (UTC).
    cases = [("solarops_ons_daily", "ons", {"as_of": datetime.now(UTC).strftime("%Y-%m-%d")})]
for dag, scenario, conf in cases:
    run_id = f"{args.mode}-{kind}-{scenario}-{stamp}"
    command("dags", "unpause", dag)
    try:
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
    finally:
        command("dags", "pause", dag)
print(
    f"Completed {'ons' if args.ons else args.source_kind}: " + ", ".join(case[1] for case in cases),
    flush=True,
)
