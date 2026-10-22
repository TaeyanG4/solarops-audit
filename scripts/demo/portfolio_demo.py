"""An isolated, offline failure-and-recovery demo with executable assertions."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from solarops.api.readmodels import run_history
from solarops.config import Settings
from solarops.fixtures import generate
from solarops.pipeline import ingest
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog

parser = argparse.ArgumentParser()
parser.add_argument(
    "--output",
    type=Path,
    default=Path("data") / ("portfolio-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S")),
)
parser.add_argument("--serve", action="store_true")
parser.add_argument("--port", type=int, default=8503)
args = parser.parse_args()
root = args.output.resolve()
if root.exists():
    parser.error("Output already exists; use a new directory to preserve earlier evidence")
settings = Settings(
    root=root,
    database_url="sqlite:///" + (root / "solarops.db").as_posix(),
    s3_endpoint=None,
    org="demo",
    timezone="UTC",
)
paths = generate(root / "fixtures")
catalog = Catalog(settings)


def execute(fail_at=None):
    return ingest(
        settings,
        paths["metadata"],
        paths["inverter"],
        paths["station"],
        "DEMO_01",
        "2024-04-01",
        "2024-04-08",
        "portfolio-v1",
        fail_at=fail_at,
    )


def hashes():
    return {
        r["partition_id"]: r["payload"]["logical_content_hash"] for r in catalog.snapshot("demo")
    }


first = execute()
before = hashes()
try:
    execute("during_commit")
except RuntimeError as exc:
    if str(exc) != "INJECTED_DURING_COMMIT":
        raise
else:
    raise RuntimeError("Fault injection did not occur")
if hashes() != before:
    raise RuntimeError("Failed transaction changed active data")
retry = execute()
if hashes() != before or len(before) != 7:
    raise RuntimeError("Replay is not logically identical")
report = build_report(settings, "2024-04", "DEMO_01", "synthetic")
evidence = {
    "dataset": "synthetic only; no network or customer data",
    "failed_publish_kept_active_data": True,
    "replay_hashes_identical": True,
    "active_partitions": len(before),
    "logical_hashes": before,
    "first_batch": first["batch_id"],
    "retry_batch": retry["batch_id"],
    "batch_status_counts": run_history(catalog, "batch")["status_counts"],
    "report": report,
}
(root / "evidence.json").write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(evidence, ensure_ascii=False, indent=2))
if args.serve:
    import uvicorn

    from solarops.api.app import create_app

    uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port)
