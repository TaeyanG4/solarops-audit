"""Copy one downloaded public plant into the existing kind PVC without overwrites."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--plant", required=True)
parser.add_argument("--source-dir", type=Path, default=Path("data/source"))
args = parser.parse_args()
if not re.fullmatch(r"PS_[0-9]{3}", args.plant):
    parser.error("Expected public plant ID such as PS_001")
root = Path(__file__).resolve().parents[2]
source = args.source_dir.resolve()
files = [
    "BR-PVGen_metadata.csv",
    f"inverter/BR-PVGen_inverter/{args.plant}.csv",
    f"station/BR-PVGen_meteorological/{args.plant}.csv",
]
for name in files:
    path = source / name
    if not path.resolve().is_relative_to(source) or not path.is_file():
        parser.error(f"Missing or unsafe source: {name}")

kubectl = ["kubectl", "--kubeconfig", str(root / "artifacts/kubeconfig"), "-n", "solarops"]
pod = "solarops-source-" + uuid.uuid4().hex[:10]
spec = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {"name": pod},
    "spec": {
        "restartPolicy": "Never",
        "activeDeadlineSeconds": 600,
        "securityContext": {"runAsUser": 10001, "runAsGroup": 10001, "fsGroup": 10001},
        "containers": [
            {
                "name": "stage",
                "image": "solarops-worker:0.5.2",
                "imagePullPolicy": "IfNotPresent",
                "command": [
                    "python",
                    "-c",
                    "import time; from pathlib import Path\nwhile not Path('/tmp/done').exists(): time.sleep(1)",
                ],
                "securityContext": {
                    "readOnlyRootFilesystem": True,
                    "allowPrivilegeEscalation": False,
                    "capabilities": {"drop": ["ALL"]},
                },
                "resources": {
                    "requests": {"cpu": "100m", "memory": "64Mi"},
                    "limits": {"cpu": "1", "memory": "256Mi"},
                },
                "volumeMounts": [
                    {"name": "data", "mountPath": "/data"},
                    {"name": "tmp", "mountPath": "/tmp"},
                ],
            }
        ],
        "volumes": [
            {"name": "data", "persistentVolumeClaim": {"claimName": "solarops-data"}},
            {"name": "tmp", "emptyDir": {}},
        ],
    },
}
subprocess.run(kubectl + ["create", "-f", "-"], input=json.dumps(spec), text=True, check=True)
remote = kubectl + ["exec", "-i", pod, "--", "python", "-c"]
check_code = """
import hashlib, sys
from pathlib import Path
root = Path('/data/source').resolve()
p = root / sys.argv[1]
assert p.resolve().is_relative_to(root), 'SOURCE_PATH_OUTSIDE_ROOT'
if p.exists():
    with p.open('rb') as f: digest = hashlib.file_digest(f, 'sha256').hexdigest()
    assert digest == sys.argv[2], 'EXISTING_SOURCE_CONFLICT: choose a separate PVC/source root'
    print('verified')
else:
    print('missing')
"""
write_code = """
import hashlib, os, shutil, sys, uuid
from pathlib import Path
root = Path('/data/source').resolve()
target = root / sys.argv[1]
assert target.resolve().is_relative_to(root), 'SOURCE_PATH_OUTSIDE_ROOT'
staging = Path('/data/source-staging') / uuid.uuid4().hex
staging.parent.mkdir(parents=True, exist_ok=True)
with staging.open('xb') as out:
    shutil.copyfileobj(sys.stdin.buffer, out, 1024 * 1024)
    out.flush()
    os.fsync(out.fileno())
with staging.open('rb') as f: digest = hashlib.file_digest(f, 'sha256').hexdigest()
assert digest == sys.argv[2], 'SOURCE_CHECKSUM_MISMATCH'
target.parent.mkdir(parents=True, exist_ok=True)
try:
    os.link(staging, target)  # Atomic no-overwrite publication on the same PVC.
except FileExistsError:
    with target.open('rb') as f: existing = hashlib.file_digest(f, 'sha256').hexdigest()
    assert existing == digest, 'EXISTING_SOURCE_CONFLICT'
print('staged')
"""
try:
    subprocess.run(
        kubectl + ["wait", "--for=condition=Ready", "pod/" + pod, "--timeout=180s"], check=True
    )
    for name in files:
        with (source / name).open("rb") as inp:
            hasher = hashlib.sha256()
            for block in iter(lambda: inp.read(1024 * 1024), b""):
                hasher.update(block)
            digest = hasher.hexdigest()
        check = subprocess.run(
            remote + [check_code, name, digest], capture_output=True, text=True, check=True
        )
        if check.stdout.strip() != "verified":
            with (source / name).open("rb") as inp:
                subprocess.run(remote + [write_code, name, digest], stdin=inp, check=True)
        print(json.dumps({"file": name, "sha256": digest, "pod": pod}), flush=True)
finally:
    # End only this helper process; keep the completed Pod and all source/staging files.
    subprocess.run(remote + ["from pathlib import Path; Path('/tmp/done').touch()"], check=False)
