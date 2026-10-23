"""Release and allowlisted execution identity, never arbitrary environment data."""

import json
import os
import subprocess
from functools import lru_cache
from pathlib import Path

RELEASE = json.loads(Path(__file__).with_name("release.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def release_info():
    revision = os.getenv("SOLAROPS_BUILD_REVISION")
    dirty = None
    root = Path(__file__).resolve().parents[2]
    if not revision and (root / ".git").exists():
        try:
            revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=5
            ).strip()
            dirty = bool(
                subprocess.check_output(
                    [
                        "git",
                        "status",
                        "--porcelain",
                        "--",
                        "src",
                        "dags",
                        "infra",
                        "pyproject.toml",
                        "uv.lock",
                    ],
                    cwd=root,
                    text=True,
                    timeout=5,
                ).strip()
            )
        except (OSError, subprocess.SubprocessError):
            revision = None
    return {**RELEASE, "git_revision": revision or "unrecorded", "source_dirty": dirty}


def execution_context():
    fields = {
        "dag_id": "SOLAROPS_DAG_ID",
        "dag_run_id": "SOLAROPS_DAG_RUN_ID",
        "task_id": "SOLAROPS_TASK_ID",
        "task_attempt": "SOLAROPS_TASK_ATTEMPT",
        "pod_uid": "SOLAROPS_POD_UID",
        "pod_name": "SOLAROPS_POD_NAME",
        "namespace": "SOLAROPS_POD_NAMESPACE",
    }
    return {key: os.environ[name][:512] for key, name in fields.items() if os.getenv(name)}
