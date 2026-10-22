"""Compare every public partition across native and real service backends."""

import json
from pathlib import Path

from solarops.config import Settings
from solarops.storage.postgres import Catalog

values = dict(
    line.split("=", 1)
    for line in Path(".env").read_text().splitlines()
    if line and not line.startswith("#")
)
native = Settings(root=Path("data").resolve(), s3_endpoint=None)
service = Settings(
    root=Path("data/service-full").resolve(),
    database_url=f"postgresql+psycopg://solarops:{values['APP_DB_PASSWORD']}@127.0.0.1:55432/solarops",
    s3_endpoint=None,
)


def inventory(settings):
    rows = [r for r in Catalog(settings).snapshot("demo") if r["plant_id"].startswith("PS_")]
    mapping = {
        (r["plant_id"], r["partition_id"]): (r["payload"]["logical_content_hash"], r["metric"])
        for r in rows
    }
    return rows, mapping


left, left_map = inventory(native)
right, right_map = inventory(service)
assert left_map == right_map
summary = {
    "identical": True,
    "public_plants": len({r["plant_id"] for r in right}),
    "public_partitions": len(right),
    "inverter_rows": sum(r["payload"]["row_count"] for r in right),
    "all_logical_hashes_and_metrics_equal": True,
}
Path("artifacts/catalog-parity.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
