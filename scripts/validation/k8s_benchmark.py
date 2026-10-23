"""Actual Airflow KPO public four-day benchmark at concurrency 1/2; retain evidence.

Creates dedicated databases/buckets/secrets, never changes the demo publications.
Run with Python 3.12 on Windows (WSL kubectl) or Linux (kubectl).
"""

import base64
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
RELEASE = json.loads((ROOT / "src/solarops/release.json").read_text())
KUBE = (["wsl.exe", "-d", "Ubuntu-22.04", "--"] if os.name == "nt" else []) + [
    "kubectl",
    "--kubeconfig",
    "/mnt/h/dev/solarops_audit/artifacts/kubeconfig"
    if os.name == "nt"
    else str(ROOT / "artifacts/kubeconfig"),
    "--context",
    "kind-solarops",
    "-n",
    "solarops",
]
STAMP = str(int(time.time()))
OUT = ROOT / "artifacts" / ("dag-benchmark-" + STAMP)
OUT.mkdir(parents=True)


def command(*args, data=None):
    result = subprocess.run(KUBE + list(args), input=data, text=True, capture_output=True)
    if result.returncode:
        # Secrets may have been supplied on stdin; never echo command input.
        raise RuntimeError("Kubernetes command failed: " + result.stderr[:500])
    return result.stdout


def sql(deployment, db, query):
    user = "airflow" if db == "airflow" else "solarops"
    return command(
        "exec", "deployment/" + deployment, "--", "psql", "-U", user, "-d", db, "-At", "-c", query
    ).strip()


def airflow(*args):
    return command("exec", "airflow-scheduler-0", "-c", "scheduler", "--", "airflow", *args)


def snapshot(probe):
    code = """
import json
from sqlalchemy import text
from solarops.config import Settings
from solarops.storage.postgres import Catalog
from solarops.storage.minio import ObjectStore
s=Settings(); c=Catalog(s,read_only=True); store=ObjectStore(s,initialize=False)
with c.engine.connect() as conn:
 row=dict(conn.execute(text("SELECT xact_commit,xact_rollback,blks_read,blks_hit,tup_returned,tup_fetched,tup_inserted,tup_updated FROM pg_stat_database WHERE datname=current_database()")).mappings().one())
objects=[o for page in store.client.get_paginator('list_objects_v2').paginate(Bucket=store.bucket) for o in page.get('Contents',[])]
print(json.dumps({'db':row,'s3_objects':len(objects),'s3_bytes':sum(o['Size'] for o in objects)}))
"""
    return json.loads(command("exec", probe, "--", "python", "-c", code))


def infra_sample():
    raw = json.loads(
        command("get", "--raw", "/api/v1/nodes/solarops-control-plane/proxy/stats/summary")
    )
    return {
        p["podRef"]["name"]: {
            "cpu_ns": p.get("cpu", {}).get("usageCoreNanoSeconds", 0),
            "memory_bytes": p.get("memory", {}).get("workingSetBytes", 0),
        }
        for p in raw["pods"]
        if p["podRef"]["namespace"] == "solarops"
        and p["podRef"]["name"].startswith(("app-db-", "minio-"))
    }


def prepare(concurrency):
    db = f"solarops_benchmark_{concurrency}_{STAMP}"
    secret = f"solarops-benchmark-{concurrency}"
    sql("app-db", "solarops", f"CREATE DATABASE {db}")
    source = json.loads(command("get", "secret", "solarops-app", "-o", "json"))["data"]
    values = {k: base64.b64decode(v).decode() for k, v in source.items()}
    values["SOLAROPS_DATABASE_URL"] = (
        make_url(values["SOLAROPS_DATABASE_URL"])
        .set(database=db)
        .render_as_string(hide_password=False)
    )
    values["SOLAROPS_S3_BUCKET"] = db.replace("_", "-")
    values["SOLAROPS_ORG"] = "demo"
    command(
        "apply",
        "-f",
        "-",
        data=json.dumps(
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {"name": secret},
                "stringData": values,
            }
        ),
    )
    probe = f"benchmark-probe-{concurrency}-{STAMP}"
    code = """
import time
from pathlib import Path
from solarops.config import Settings
from solarops.storage.postgres import Catalog
from solarops.storage.minio import ObjectStore
s=Settings(); Catalog(s).engine.dispose(); ObjectStore(s)
Path('/tmp/ready').touch()
while not Path('/tmp/done').exists(): time.sleep(1)
"""
    command(
        "create",
        "-f",
        "-",
        data=json.dumps(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": probe},
                "spec": {
                    "restartPolicy": "Never",
                    "activeDeadlineSeconds": 1200,
                    "securityContext": {"runAsUser": 10001, "runAsGroup": 10001, "fsGroup": 10001},
                    "containers": [
                        {
                            "name": "probe",
                            "image": RELEASE["worker_image"],
                            "imagePullPolicy": "IfNotPresent",
                            "command": ["python", "-c", code],
                            "envFrom": [{"secretRef": {"name": secret}}],
                            "env": [{"name": "SOLAROPS_DATA_DIR", "value": "/tmp/probe"}],
                            "securityContext": {
                                "readOnlyRootFilesystem": True,
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "resources": {
                                "requests": {"cpu": "100m", "memory": "128Mi"},
                                "limits": {"cpu": "1", "memory": "512Mi"},
                            },
                            "readinessProbe": {
                                "exec": {"command": ["test", "-f", "/tmp/ready"]},
                                "periodSeconds": 2,
                            },
                            "volumeMounts": [{"name": "tmp", "mountPath": "/tmp"}],
                        }
                    ],
                    "volumes": [{"name": "tmp", "emptyDir": {}}],
                },
            }
        ),
    )
    command("wait", "--for=condition=Ready", "pod/" + probe, "--timeout=120s")
    return probe, db


results = []
for concurrency in (1, 2):
    probe, db = prepare(concurrency)
    dag = f"solarops_public_benchmark_{concurrency}"
    run_id = f"benchmark-{STAMP}-{concurrency}"
    before = snapshot(probe)
    samples = [infra_sample()]
    began = time.perf_counter()
    airflow("dags", "unpause", dag)
    try:
        airflow(
            "dags",
            "trigger",
            dag,
            "--run-id",
            run_id,
            "--conf",
            json.dumps({"benchmark_id": run_id}),
        )
        print(json.dumps({"started": run_id, "database": db}), flush=True)
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            row = sql(
                "airflow-db",
                "airflow",
                f"SELECT row_to_json(r) FROM (SELECT state,start_date,end_date FROM dag_run WHERE dag_id='{dag}' AND run_id='{run_id}') r",
            )
            state = json.loads(row) if row else {}
            samples.append(infra_sample())
            if state.get("state") in ("success", "failed"):
                break
            time.sleep(5)
        else:
            raise TimeoutError(run_id)
        wall = time.perf_counter() - began
        after = snapshot(probe)
        pods = json.loads(command("get", "pods", "-l", "dag_id=" + dag, "-o", "json"))["items"]
        measurements = []
        for pod in pods:
            if not pod["metadata"]["labels"].get("run_id", "").startswith(run_id):
                continue
            log = command("logs", pod["metadata"]["name"])
            (OUT / (pod["metadata"]["name"] + ".log")).write_text(log, encoding="utf-8")
            parsed = None
            for index, char in enumerate(log):
                if char != "{":
                    continue
                try:
                    candidate, _ = json.JSONDecoder().raw_decode(log[index:])
                    if isinstance(candidate, dict) and "profile" in candidate:
                        parsed = candidate
                        break
                except ValueError:
                    pass
            if not parsed:
                raise RuntimeError("Missing worker profile: " + pod["metadata"]["name"])
            measurements.append(
                {
                    "task": pod["metadata"]["labels"]["task_id"],
                    "pod": pod["metadata"]["name"],
                    **parsed,
                }
            )
        measurements.sort(key=lambda m: m["task"])
        start = datetime.fromisoformat(state["start_date"])
        end = datetime.fromisoformat(state["end_date"])
        result = {
            "concurrency": concurrency,
            "dag_run": run_id,
            "state": state,
            "database": db,
            "wall_seconds_with_trigger_and_poll": wall,
            "dag_wall_seconds": (end - start).total_seconds(),
            "worker_cpu_seconds": sum(m["profile"]["cpu_seconds"] for m in measurements),
            "peak_worker_rss_kib": max(m["profile"]["peak_rss_kib"] for m in measurements),
            "rows": sum(m["rows"] for m in measurements),
            "measurements": measurements,
            "db_delta": {k: after["db"][k] - before["db"][k] for k in before["db"]},
            "s3_new_objects": after["s3_objects"] - before["s3_objects"],
            "s3_new_bytes": after["s3_bytes"] - before["s3_bytes"],
            "service_samples": samples,
            "service_usage": {
                name: {
                    "cpu_seconds": (samples[-1][name]["cpu_ns"] - samples[0][name]["cpu_ns"]) / 1e9,
                    "sampled_peak_memory_bytes": max(
                        s.get(name, {}).get("memory_bytes", 0) for s in samples
                    ),
                }
                for name in samples[0]
            },
        }
        results.append(result)
        (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {k: v for k, v in result.items() if k not in ("measurements", "service_samples")}
            ),
            flush=True,
        )
        assert state["state"] == "success" and len(measurements) == 4
        assert all(len(m["results"]) == 1 for m in measurements)
        assert result["peak_worker_rss_kib"] < 2 * 1024**2 and result["dag_wall_seconds"] < 600
    finally:
        airflow("dags", "pause", dag)
        command(
            "exec",
            probe,
            "--",
            "python",
            "-c",
            "from pathlib import Path;Path('/tmp/done').touch()",
        )
assert (
    len(
        {
            json.dumps(
                [(m["task"], [r["logical_hash"] for r in m["results"]]) for m in x["measurements"]]
            )
            for x in results
        }
    )
    == 1
)
improvement = 1 - results[1]["dag_wall_seconds"] / results[0]["dag_wall_seconds"]
summary = {
    "logical_hashes_equal": True,
    "improvement_fraction": improvement,
    "recommend_parallel_2": improvement >= 0.15,
    "scope": "single host, one serial then one parallel run, filesystem cache and scheduler effects included; net S3 size is not request latency",
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary), flush=True)
