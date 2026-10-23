"""One release specification; check/sync declarations or build attributable images."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "src/solarops/release.json"


def check_release(sync=False):
    release = json.loads(SPEC.read_text(encoding="utf-8"))
    version = release["app_version"]
    assert release["release_id"] == version
    assert release["worker_image"] == f"solarops-worker:{version}"
    assert release["airflow_image"] == f"solarops-airflow:{version}"
    paths = [
        "Makefile",
        "infra/compose/compose.yaml",
        "infra/helm/airflow-values.yaml",
        "scripts/ops/k8s-deploy.sh",
        "scripts/ops/k8s-refresh.sh",
        "scripts/ops/k8s-stage-public.py",
        "scripts/validation/k8s_benchmark.py",
        "pyproject.toml",
    ]
    for name in paths:
        path = ROOT / name
        before = path.read_text(encoding="utf-8")
        after = re.sub(
            r"solarops-(worker|airflow):[\w.\-]+", lambda m: release[m[1] + "_image"], before
        )
        if name == "infra/helm/airflow-values.yaml":
            after = re.sub(r'(defaultAirflowTag: |tag: )"[^"]+"', rf'\g<1>"{version}"', after)
        if name == "pyproject.toml":
            after = re.sub(r'^version = "[^"]+"', f'version = "{version}"', after, flags=re.M)
        if sync and after != before:
            path.write_text(after, encoding="utf-8", newline="\n")
        else:
            assert after == before, f"Release drift: {name}; run release.py sync"
    constraints = (ROOT / release["airflow_constraints"]).read_bytes()
    assert hashlib.sha256(constraints).hexdigest() == release["airflow_constraints_sha256"]
    pinned = constraints.decode("utf-8-sig").splitlines()
    for name, ver in (
        ("apache-airflow", release["airflow_version"]),
        ("apache-airflow-providers-cncf-kubernetes", release["kubernetes_provider_version"]),
    ):
        assert f"{name}=={ver}" in pinned
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    assert (
        next(p["version"] for p in lock["package"] if p["name"] == "solarops-audit") == version
    ), "Run uv lock"
    return release


def build(release):
    # Never label dirty source with a clean commit ID.
    dirty = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "src",
            "dags",
            "infra",
            "scripts",
            "pyproject.toml",
            "uv.lock",
        ],
        cwd=ROOT,
        text=True,
    ).strip()
    if dirty:
        raise RuntimeError("Commit implementation files before building a release")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    evidence = {"release": release, "git_revision": revision, "images": {}}
    for target in ("worker", "airflow"):
        image = release[target + "_image"]
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                "infra/docker/Dockerfile",
                "--target",
                target,
                "--build-arg",
                "SOURCE_REVISION=" + revision,
                "-t",
                image,
                ".",
            ],
            cwd=ROOT,
            check=True,
        )
        identity = subprocess.check_output(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True
        ).strip()
        evidence["images"][image] = identity
    output = ROOT / "artifacts/releases" / (release["release_id"] + "-" + revision[:12] + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2)
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "sync", "build"], default="check", nargs="?")
    args = parser.parse_args()
    specification = check_release(args.command == "sync")
    if args.command == "build":
        build(specification)
    else:
        print("Release declarations aligned:", specification["release_id"])
