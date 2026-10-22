"""Isolated synthetic SQLite/file restore drill, not a live-service backup tool."""

import argparse
import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select, update

from solarops.acquisition.brpvgen import checksum
from solarops.api.app import create_app
from solarops.config import Settings
from solarops.fixtures import generate
from solarops.pipeline import ingest
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog, metadata, sources


def settings_for(root):
    return Settings(
        root=root,
        database_url="sqlite:///" + (root / "solarops.db").as_posix(),
        s3_endpoint=None,
        org="demo",
        timezone="UTC",
    )


def file_inventory(root):
    return {
        p.relative_to(root).as_posix(): checksum(p)
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name not in {"solarops.db", "solarops.db-wal", "solarops.db-shm"}
    }


def validate_inventory(root, inventory):
    for name, digest in inventory.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Missing or out-of-root backup file")
        if checksum(path) != digest:
            raise ValueError("Backup checksum mismatch")


def relocate(value, original, restored):
    # Only used on this drill's own generated catalog. Historical artifact bytes stay exact.
    if isinstance(value, dict):
        return {k: relocate(v, original, restored) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v, original, restored) for v in value]
    if isinstance(value, str) and value.startswith(str(original)):
        path = Path(value)
        if path.is_relative_to(original):
            return str(restored / path.relative_to(original))
    return value


def hashes(settings):
    catalog = Catalog(settings)
    try:
        return {
            r["partition_id"]: r["payload"]["logical_content_hash"]
            for r in catalog.snapshot(settings.org)
        }
    finally:
        catalog.engine.dispose()


def run_drill(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    original, backup, restored = (output / name for name in ("original", "backup", "restored"))
    settings = settings_for(original)
    paths = generate(original / "fixtures")

    def ingest_paths(target, inputs):
        return ingest(
            target,
            inputs["metadata"],
            inputs["inverter"],
            inputs["station"],
            "DEMO_01",
            "2024-04-01",
            "2024-04-08",
            "restore-drill-v1",
        )

    ingest_paths(settings, paths)
    report = build_report(settings, "2024-04", "DEMO_01", "synthetic")
    expected = hashes(settings)
    assert len(expected) == 7

    # All producer calls have finished. There are no concurrent writers in this isolated root.
    before = file_inventory(original)
    backup.mkdir()
    with sqlite3.connect((original / "solarops.db").as_uri() + "?mode=ro", uri=True) as src:
        with sqlite3.connect(backup / "solarops.db") as dst:
            src.backup(dst)
            assert dst.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    for name in before:
        target = backup / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with (original / name).open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    assert file_inventory(original) == before
    inventory = dict(before, **{"solarops.db": checksum(backup / "solarops.db")})
    validate_inventory(backup, inventory)
    (output / "backup-manifest.json").write_text(
        json.dumps({"original_root": str(original), "files": inventory}, indent=2),
        encoding="utf-8",
    )

    # A deliberately damaged extra copy must be rejected; originals/backups remain untouched.
    damaged = output / "damaged-probe"
    damaged.mkdir()
    (damaged / "solarops.db").write_bytes(b"synthetic damage probe")
    try:
        validate_inventory(damaged, {"solarops.db": inventory["solarops.db"]})
    except ValueError as exc:
        assert str(exc) == "Backup checksum mismatch"
    else:
        raise AssertionError("Corrupted backup was accepted")

    shutil.copytree(backup, restored)  # Destination must not exist; no overwrite or deletion.
    validate_inventory(restored, inventory)
    target_settings = settings_for(restored)
    catalog = Catalog(target_settings)
    with catalog.engine.begin() as conn:
        for table in metadata.sorted_tables:
            for row in conn.execute(select(table)).mappings().all():
                payload = relocate(row["payload"], original, restored)
                conn.execute(
                    update(table)
                    .where(*(table.c[c.name] == row[c.name] for c in table.primary_key))
                    .values(payload=payload)
                )
        raw = {
            row["payload"]["dataset_kind"]: Path(row["payload"]["raw_uri"])
            for row in conn.execute(select(sources)).mappings()
        }
        for row in conn.execute(select(sources)).mappings():
            assert checksum(Path(row["payload"]["raw_uri"])) == row["sha256"]
    assert all(p.is_relative_to(restored) for p in raw.values())
    catalog.engine.dispose()
    assert hashes(target_settings) == expected
    validate_inventory(restored, before)  # Original artifacts are still byte-for-byte identical.

    with TestClient(create_app(target_settings)) as client:
        overview = client.get("/api/v1/overview?period=2024-04&source_kind=synthetic")
        assert overview.status_code == 200
        assert overview.json()["summary"]["partition_count"] == 7
        series = client.get("/api/v1/plants/DEMO_01/series?day=2024-04-01")
        assert series.status_code == 200 and len(series.json()["items"]) == 96
        for filename in ("report.html", "metrics.csv", "manifest.json"):
            response = client.get(f"/reports/{report['report_id']}/{filename}")
            assert response.status_code == 200
            assert (
                response.content
                == (backup / "reports/demo" / report["report_id"] / filename).read_bytes()
            )

    ingest_paths(target_settings, raw)
    assert hashes(target_settings) == expected
    new_report = build_report(target_settings, "2024-04", "DEMO_01", "synthetic")
    assert new_report["report_id"] != report["report_id"]
    assert file_inventory(original) == before
    validate_inventory(backup, inventory)
    evidence = {
        "scope": "synthetic, quiesced SQLite + local files; same-host isolated relocation",
        "concurrent_or_postgres_minio_backup_validated": False,
        "active_partitions": len(expected),
        "backed_up_files_including_database": len(inventory),
        "sqlite_integrity": "ok",
        "backup_hashes_verified": True,
        "damaged_copy_rejected": True,
        "restored_api_and_historical_reports_verified": True,
        "restored_raw_replay_hashes_equal": True,
        "original_artifacts_unchanged": True,
        "original_root": str(original),
        "restored_root": str(restored),
        "historical_report_id": report["report_id"],
        "new_report_id": new_report["report_id"],
        "note": "Restored catalog paths were relocated; historical manifests retain original provenance URIs. Resolve these with the root mapping above. Original backup DB is preserved.",
    }
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data") / ("restore-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S")),
    )
    print(json.dumps(run_drill(parser.parse_args().output), indent=2))
