"""Capture v1 public evidence, then compare v2 without changing either version."""

import argparse
import json
import os
from pathlib import Path

from sqlalchemy import select

from solarops.config import CALCULATION_VERSION, Settings
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active, metrics


def inventory(catalog, version):
    statement = (
        select(active, metrics.c.payload.label("metric"))
        .join(metrics, active.c.run_id == metrics.c.run_id)
        .where(
            active.c.org_id == catalog.settings.org,
            active.c.report_timezone == "UTC",
            active.c.calculation_version == version,
            active.c.payload["source_objects"][0]["source_kind"].as_string() == "public",
        )
        .order_by(active.c.plant_id, active.c.partition_id)
    )
    with catalog.engine.connect() as conn:
        return {
            r["plant_id"] + "/" + r["partition_id"]: {
                "run_id": r["run_id"],
                "hash": r["payload"]["logical_content_hash"],
                "source_hashes": [s["sha256"] for s in r["payload"]["source_objects"]],
                "series_uri": r["payload"]["series_uri"],
                "metric": r["metric"],
            }
            for r in conn.execute(statement).mappings()
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--services", action="store_true")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.services:
        values = dict(
            line.split("=", 1)
            for line in Path(".env").read_text().splitlines()
            if line and not line.startswith("#")
        )
        os.environ.update(
            SOLAROPS_DATA_DIR="data/service-full",
            SOLAROPS_DATABASE_URL=f"postgresql+psycopg://solarops:{values['APP_DB_PASSWORD']}@127.0.0.1:55432/solarops",
            SOLAROPS_S3_ENDPOINT="http://127.0.0.1:59000",
            SOLAROPS_S3_ACCESS_KEY=values["MINIO_ROOT_USER"],
            SOLAROPS_S3_SECRET_KEY=values["MINIO_ROOT_PASSWORD"],
        )
    settings = Settings()
    catalog = Catalog(settings)
    previous = inventory(catalog, "energy-interval-v1")
    if not previous:
        raise ValueError("No v1 public UTC partitions to compare")
    if args.capture:
        with args.baseline.open("x", encoding="utf-8") as out:
            json.dump(previous, out, ensure_ascii=False)
        print(json.dumps({"baseline_partitions": len(previous), "path": str(args.baseline)}))
        return
    if not args.output or args.output.exists():
        raise ValueError("Choose a new --output file")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    assert previous == baseline, "Existing v1 pointers, hashes or metrics changed"
    current = inventory(catalog, CALCULATION_VERSION)
    assert current.keys() == baseline.keys(), "Partition inventory differs"
    for key, before in baseline.items():
        after = current[key]
        assert after["source_hashes"] == before["source_hashes"], key
        assert after["hash"] != before["hash"], "Version must be represented in the hash"
        assert {k: v for k, v in after["metric"].items() if k != "calculation_version"} == {
            k: v for k, v in before["metric"].items() if k != "calculation_version"
        }, key
    store = ObjectStore(settings)

    def series(uri):
        if uri.startswith("s3://"):
            bucket, key = uri[5:].split("/", 1)
            assert bucket == store.bucket
            return json.loads(store.client.get_object(Bucket=bucket, Key=key)["Body"].read())
        return json.loads(Path(uri).read_text(encoding="utf-8"))

    # Deterministic cross-plant sample, not a claim that every time series was compared.
    keys = list(current)
    sample = keys[:: max(1, len(keys) // 30)]
    corrected, checked_slots = 0, 0
    for key in sample:
        left, right = series(baseline[key]["series_uri"]), series(current[key]["series_uri"])
        assert len(left) == len(right), key
        for old, new in zip(left, right, strict=True):
            checked_slots += 1
            if old != new:
                assert old["power_kw"] == 0 and new["power_kw"] is None, key
                assert dict(old, power_kw=None) == new, key
                assert new["assessment"] == "INSUFFICIENT_DATA", key
                corrected += 1
    summary = {
        "calculation_version": CALCULATION_VERSION,
        "public_plants": len({key.split("/")[0] for key in current}),
        "partitions": len(current),
        "v1_unchanged": True,
        "all_daily_metrics_equal_except_version": True,
        "all_source_hashes_equal": True,
        "sampled_series": len(sample),
        "sampled_slots": checked_slots,
        "sampled_zero_to_null_corrections": corrected,
        "series_sample_keys": sample,
    }
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(summary, out, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
