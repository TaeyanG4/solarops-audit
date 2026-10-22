"""Terminate only the demo worker process; retain its Pod and all data/evidence."""

import json
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
kube = ["kubectl", "--kubeconfig", str(root / "artifacts/kubeconfig"), "-n", "solarops"]
airflow = kube + ["exec", "airflow-scheduler-0", "-c", "scheduler", "--", "airflow"]
run_id = "pod-crash-" + str(int(time.time()))
subprocess.run(
    airflow + ["dags", "unpause", "solarops_backfill_manual"], check=True, capture_output=True
)
subprocess.run(
    airflow
    + [
        "dags",
        "trigger",
        "solarops_backfill_manual",
        "--run-id",
        run_id,
        "--conf",
        json.dumps(
            {
                "test_delay": "30",
                "dry_run": "false",
                "from_date": "2024-04-01",
                "to_date": "2024-04-02",
            }
        ),
    ],
    check=True,
    capture_output=True,
)
deadline = time.monotonic() + 300
killed = None
while time.monotonic() < deadline:
    pods = json.loads(
        subprocess.check_output(
            kube
            + [
                "get",
                "pods",
                "-l",
                "dag_id=solarops_backfill_manual,task_id=replay_validate_publish",
                "-o",
                "json",
            ],
            text=True,
        )
    )["items"]
    running = [
        p
        for p in pods
        if p["status"].get("phase") == "Running"
        and p["metadata"]["labels"].get("run_id", "").startswith(run_id)
    ]
    if running:
        killed = running[0]["metadata"]["name"]
        # PID 1 is solarops in this explicitly-created task container; no files are removed.
        subprocess.run(
            kube
            + ["exec", killed, "--", "python", "-c", "import os,signal;os.kill(1,signal.SIGINT)"],
            capture_output=True,
        )
        print(json.dumps({"terminated_demo_worker": killed, "run_id": run_id}), flush=True)
        break
    time.sleep(2)
if not killed:
    raise TimeoutError("No matching demo worker started")
while time.monotonic() < deadline:
    runs = json.loads(
        subprocess.check_output(
            airflow + ["dags", "list-runs", "solarops_backfill_manual", "--output", "json"],
            text=True,
        )
    )
    row = next(r for r in runs if r["run_id"] == run_id)
    if row["state"] in ("success", "failed"):
        pod = json.loads(
            subprocess.check_output(kube + ["get", "pod", killed, "-o", "json"], text=True)
        )
        terminated = pod["status"]["containerStatuses"][0]["state"].get("terminated", {})
        assert terminated.get("exitCode", 0) != 0, "Worker did not actually terminate abnormally"
        evidence = {"pod": killed, "termination": terminated, "run": row}
        (root / "artifacts/k8s-pod-failure.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8"
        )
        print(json.dumps(evidence), flush=True)
        assert row["state"] == "success"
        break
    time.sleep(5)
else:
    raise TimeoutError(run_id)
subprocess.run(
    airflow + ["dags", "pause", "solarops_backfill_manual"], check=True, capture_output=True
)
