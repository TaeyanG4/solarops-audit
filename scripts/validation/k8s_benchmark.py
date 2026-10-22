"""Fixed four-day workload on 1/2/4 concurrent Pods; no data deletion."""

import json
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[2]
kube = ["kubectl", "--kubeconfig", str(root / "artifacts/kubeconfig"), "-n", "solarops"]
stamp = str(int(time.time()))
code = """
import json,os,resource,time
from pathlib import Path
from solarops.config import Settings
from solarops.pipeline import ingest
start=time.perf_counter()
i=int(os.environ['JOB_COMPLETION_INDEX'])+1
p=Path('/data/fixtures/synthetic-v1')
r=ingest(Settings(),p/'metadata.csv',p/'inverter.csv',p/'station.csv','DEMO_01',f'2024-04-{i:02d}',f'2024-04-{i+1:02d}','synthetic-v1')
u=resource.getrusage(resource.RUSAGE_SELF)
print(json.dumps({'day':i,'seconds':time.perf_counter()-start,'max_rss_kib':u.ru_maxrss,'cpu_seconds':u.ru_utime+u.ru_stime,'rows':r['rows'],'hashes':[x['logical_hash'] for x in r['results']]}))
"""
results = []
for concurrency in (1, 2, 4):
    name = f"solarops-bench-{stamp}-{concurrency}"
    pod = {
        "restartPolicy": "Never",
        "serviceAccountName": "solarops-worker",
        "securityContext": {"runAsUser": 10001, "runAsGroup": 10001, "fsGroup": 10001},
        "containers": [
            {
                "name": "worker",
                "image": "solarops-worker:0.4.1",
                "imagePullPolicy": "IfNotPresent",
                "command": ["python", "-c", code],
                "envFrom": [{"secretRef": {"name": "solarops-app"}}],
                "env": [
                    {
                        "name": "JOB_COMPLETION_INDEX",
                        "valueFrom": {
                            "fieldRef": {
                                "fieldPath": "metadata.annotations['batch.kubernetes.io/job-completion-index']"
                            }
                        },
                    }
                ],
                "resources": {
                    "requests": {"cpu": "250m", "memory": "512Mi"},
                    "limits": {"cpu": "2", "memory": "2Gi"},
                },
                "volumeMounts": [{"name": "data", "mountPath": "/data"}],
            }
        ],
        "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "solarops-data"}}],
    }
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": name},
        "spec": {
            "completions": 4,
            "parallelism": concurrency,
            "completionMode": "Indexed",
            "backoffLimit": 0,
            "activeDeadlineSeconds": 300,
            "template": {"spec": pod},
        },
    }
    began = time.perf_counter()
    subprocess.run(
        kube + ["apply", "-f", "-"],
        input=json.dumps(job),
        text=True,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        kube + ["wait", "--for=condition=complete", "job/" + name, "--timeout=300s"],
        check=True,
        capture_output=True,
    )
    elapsed = time.perf_counter() - began
    pods = json.loads(
        subprocess.check_output(
            kube + ["get", "pods", "-l", "job-name=" + name, "-o", "json"], text=True
        )
    )["items"]
    measurements = []
    for p in pods:
        output = subprocess.check_output(kube + ["logs", p["metadata"]["name"]], text=True)
        measurements.append(json.loads(output.strip().splitlines()[-1]))
    result = {
        "concurrent_pods": concurrency,
        "job": name,
        "wall_seconds_including_startup": round(elapsed, 3),
        "cpu_seconds": sum(m["cpu_seconds"] for m in measurements),
        "max_worker_rss_kib": max(m["max_rss_kib"] for m in measurements),
        "rows": sum(m["rows"] for m in measurements),
        "measurements": sorted(measurements, key=lambda x: x["day"]),
        "errors": 0,
    }
    results.append(result)
    print(json.dumps(result), flush=True)
assert len({json.dumps([(m["day"], m["hashes"]) for m in r["measurements"]]) for r in results}) == 1
(root / "artifacts/k8s-benchmark.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
