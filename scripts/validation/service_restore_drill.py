"""Quiesced synthetic Postgres/MinIO logical restore in new DBs/buckets; retain all evidence."""

import argparse
import hashlib
import json
import os
import secrets as random_secrets
import subprocess
import time
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.engine import URL

from solarops import __version__
from solarops.acquisition.brpvgen import checksum
from solarops.api.app import create_app
from solarops.config import CALCULATION_VERSION, Settings
from solarops.fixtures import generate
from solarops.pipeline import canonical_hash, ingest
from solarops.reports.render import build_report
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, metadata, runs, sources


def digest(data):
    return hashlib.sha256(data).hexdigest()


def remap(value, old_bucket, new_bucket):
    if isinstance(value, dict):
        return {k: remap(v, old_bucket, new_bucket) for k, v in value.items()}
    if isinstance(value, list):
        return [remap(v, old_bucket, new_bucket) for v in value]
    prefix = f"s3://{old_bucket}/"
    if isinstance(value, str) and value.startswith(prefix):
        return f"s3://{new_bucket}/" + value[len(prefix) :]
    return value


def run_drill(output, isolated_target=False):
    owned = []
    try:
        return _run_drill(output, isolated_target, owned)
    finally:
        if owned:
            subprocess.run(["docker", "stop", *owned], check=True, capture_output=True)


def _run_drill(output, isolated_target, target_containers):
    started = time.monotonic()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    secrets = dict(
        line.split("=", 1)
        for line in Path(".env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    base = URL.create(
        "postgresql+psycopg",
        username="solarops",
        password=secrets["APP_DB_PASSWORD"],
        host="127.0.0.1",
        port=55432,
        database="solarops",
    )
    suffix = uuid.uuid4().hex[:12]
    original_db, restored_db = (f"restore_{suffix}_{kind}" for kind in ("original", "restored"))
    original_bucket, restored_bucket = (
        f"restore-{suffix}-{kind}" for kind in ("original", "restored")
    )
    org = "restore-" + suffix
    target_base = base
    target_endpoint = "http://127.0.0.1:59000"
    target_credentials = secrets
    if isolated_target:
        target_credentials = {
            "APP_DB_PASSWORD": random_secrets.token_hex(24),
            "MINIO_ROOT_USER": "restore-" + suffix,
            "MINIO_ROOT_PASSWORD": random_secrets.token_hex(24),
        }
        pg_name, s3_name = "solarops-restore-pg-" + suffix, "solarops-restore-s3-" + suffix
        for name, port, image, env, command in (
            (
                pg_name,
                5432,
                "postgres:16.10-bookworm",
                {
                    "POSTGRES_USER": "solarops",
                    "POSTGRES_DB": "solarops",
                    "POSTGRES_PASSWORD": target_credentials["APP_DB_PASSWORD"],
                },
                [],
            ),
            (
                s3_name,
                9000,
                "solarops-minio:2025-10-15-pinned",
                {
                    "MINIO_ROOT_USER": target_credentials["MINIO_ROOT_USER"],
                    "MINIO_ROOT_PASSWORD": target_credentials["MINIO_ROOT_PASSWORD"],
                },
                ["server", "/data"],
            ),
        ):
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--cpus=1",
                    "--memory=768m",
                    "-p",
                    f"127.0.0.1::{port}",
                    *[value for key in env for value in ("-e", key)],
                    image,
                    *command,
                ],
                env={**os.environ, **env},
                check=True,
                capture_output=True,
            )
            target_containers.append(name)
            # Persist owned resource names immediately, even if a later readiness check fails.
            (output / "target-containers.json").write_text(json.dumps(target_containers))
        pg_port = int(
            subprocess.check_output(["docker", "port", pg_name, "5432/tcp"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        s3_port = int(
            subprocess.check_output(["docker", "port", s3_name, "9000/tcp"], text=True)
            .strip()
            .rsplit(":", 1)[1]
        )
        target_base = base.set(port=pg_port, password=target_credentials["APP_DB_PASSWORD"])
        target_endpoint = f"http://127.0.0.1:{s3_port}"
        from urllib.request import urlopen

        for _ in range(60):
            try:
                ready = (
                    subprocess.run(
                        ["docker", "exec", pg_name, "pg_isready", "-U", "solarops"],
                        capture_output=True,
                        check=False,
                    ).returncode
                    == 0
                )
                with urlopen(target_endpoint + "/minio/health/ready", timeout=2) as response:
                    if ready and response.status == 200:
                        break
            except OSError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Isolated target not ready; owned containers retained in output")
    for url, database in ((base, original_db), (target_base, restored_db)):
        admin = create_engine(url, isolation_level="AUTOCOMMIT")
        try:
            with admin.connect() as conn:
                # Names are generated internally, never accepted from command-line input.
                conn.execute(text(f'CREATE DATABASE "{database}"'))
        finally:
            admin.dispose()
    os.environ.update(
        SOLAROPS_S3_ACCESS_KEY=secrets["MINIO_ROOT_USER"],
        SOLAROPS_S3_SECRET_KEY=secrets["MINIO_ROOT_PASSWORD"],
        SOLAROPS_S3_BUCKET=original_bucket,
    )

    def config(name, folder, url=base, endpoint="http://127.0.0.1:59000"):
        return Settings(
            root=output / folder,
            database_url=url.set(database=name).render_as_string(hide_password=False),
            s3_endpoint=endpoint,
            org=org,
            timezone="UTC",
        )

    original = config(original_db, "original")
    restored = config(restored_db, "restored", target_base, target_endpoint)
    paths = generate(original.root / "fixtures")

    def process(settings, inputs):
        return ingest(
            settings,
            inputs["metadata"],
            inputs["inverter"],
            inputs["station"],
            "DEMO_01",
            "2024-04-01",
            "2024-04-08",
            "service-restore-v1",
        )

    def hashes(settings):
        catalog = Catalog(settings)
        try:
            return {
                r["partition_id"]: r["payload"]["logical_content_hash"]
                for r in catalog.snapshot(org)
            }
        finally:
            catalog.engine.dispose()

    def catalog_hash(settings):
        catalog = Catalog(settings)
        try:
            with catalog.engine.connect() as conn:
                inventory = {
                    table.name: [
                        dict(row)
                        for row in conn.execute(
                            select(table).order_by(*table.primary_key)
                        ).mappings()
                    ]
                    for table in metadata.sorted_tables
                }
            return canonical_hash(inventory)
        finally:
            catalog.engine.dispose()

    process(original, paths)
    report = build_report(original, "2024-04", "DEMO_01", "synthetic")
    expected = hashes(original)
    original_catalog_hash = catalog_hash(original)
    assert len(expected) == 7
    catalog = Catalog(original)
    with catalog.engine.connect() as conn:
        assert not conn.execute(
            select(runs).where(runs.c.status.in_(["running", "validated"]))
        ).first()
    catalog.engine.dispose()
    store = ObjectStore(original)
    client = store.client

    def objects(bucket, connection=client):
        result = {}
        for page in connection.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for row in page.get("Contents", []):
                response = connection.get_object(Bucket=bucket, Key=row["Key"])
                body = response["Body"].read()
                response["Body"].close()
                result[row["Key"]] = {"sha256": digest(body), "size": len(body)}
        return result

    # The only producer is this process; all its writes above have completed.
    inventory = objects(original_bucket)
    compose = [
        "docker",
        "compose",
        "--env-file",
        ".env",
        "-f",
        "infra/compose/compose.yaml",
        "exec",
        "-T",
        "app-db",
    ]
    dump = output / "catalog.dump"
    with dump.open("xb") as out:
        subprocess.run(
            compose
            + ["pg_dump", "-U", "solarops", "-d", original_db, "-Fc", "--no-owner", "--no-acl"],
            stdout=out,
            check=True,
        )
    for key, info in inventory.items():
        target = output / "objects" / key
        target.parent.mkdir(parents=True, exist_ok=True)
        body = client.get_object(Bucket=original_bucket, Key=key)["Body"].read()
        assert digest(body) == info["sha256"]
        with target.open("xb") as out:
            out.write(body)
    assert objects(original_bucket) == inventory
    manifest = {
        "target_containers": target_containers,
        "isolated_target": isolated_target,
        "database_dump_sha256": checksum(dump),
        "objects": inventory,
        "original_database": original_db,
        "restored_database": restored_db,
        "original_bucket": original_bucket,
        "restored_bucket": restored_bucket,
        "org": org,
        "app_version": __version__,
        "calculation_version": CALCULATION_VERSION,
        "original_catalog_hash": original_catalog_hash,
        "postgres_dump_version": subprocess.check_output(
            compose + ["pg_dump", "--version"], text=True
        ).strip(),
        "image_ids": {
            name: subprocess.check_output(
                ["docker", "image", "inspect", "--format", "{{.Id}}", name], text=True
            ).strip()
            for name in (
                "solarops-worker:" + __version__,
                "postgres:16.10-bookworm",
                "solarops-minio:2025-10-15-pinned",
            )
        },
    }
    (output / "backup-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    restore_started = time.monotonic()
    os.environ.update(
        SOLAROPS_S3_BUCKET=restored_bucket,
        SOLAROPS_S3_ACCESS_KEY=target_credentials["MINIO_ROOT_USER"],
        SOLAROPS_S3_SECRET_KEY=target_credentials["MINIO_ROOT_PASSWORD"],
    )
    target_client = ObjectStore(restored).client
    restore_command = ["docker", "exec", "-i", target_containers[0]] if isolated_target else compose
    with dump.open("rb") as inp:
        subprocess.run(
            restore_command
            + [
                "pg_restore",
                "-U",
                "solarops",
                "-d",
                restored_db,
                "--no-owner",
                "--no-acl",
                "--exit-on-error",
                "--single-transaction",
            ],
            stdin=inp,
            check=True,
        )
    for key, info in inventory.items():
        path = output / "objects" / key
        assert checksum(path) == info["sha256"]
        target_client.upload_file(
            str(path), restored_bucket, key, ExtraArgs={"Metadata": {"sha256": info["sha256"]}}
        )
    assert objects(restored_bucket, target_client) == inventory
    catalog = Catalog(restored)
    restored.root.mkdir(parents=True, exist_ok=False)
    with catalog.engine.begin() as conn:
        for table in metadata.sorted_tables:
            for row in conn.execute(select(table)).mappings().all():
                conn.execute(
                    update(table)
                    .where(*(table.c[c.name] == row[c.name] for c in table.primary_key))
                    .values(payload=remap(row["payload"], original_bucket, restored_bucket))
                )
        inputs = {}
        for row in conn.execute(select(sources)).mappings():
            info = row["payload"]
            prefix = f"s3://{restored_bucket}/"
            assert info["raw_uri"].startswith(prefix)
            data = target_client.get_object(
                Bucket=restored_bucket, Key=info["raw_uri"][len(prefix) :]
            )["Body"].read()
            assert digest(data) == row["sha256"]
            local = restored.root / info["original_filename"]
            with local.open("xb") as out:
                out.write(data)
            inputs[info["dataset_kind"]] = local
    catalog.engine.dispose()
    assert hashes(restored) == expected
    with TestClient(create_app(restored)) as api:
        overview = api.get("/api/v1/overview?period=2024-04&source_kind=synthetic")
        assert overview.status_code == 200 and overview.json()["summary"]["partition_count"] == 7
        series = api.get("/api/v1/plants/DEMO_01/series?day=2024-04-01")
        assert series.status_code == 200 and len(series.json()["items"]) == 96
        for filename, uri in report["artifacts"].items():
            response = api.get(f"/reports/{report['report_id']}/{filename}")
            assert response.status_code == 200
            key = uri.split("/", 3)[3]
            assert digest(response.content) == inventory[key]["sha256"]
    restore_seconds = round(time.monotonic() - restore_started, 3)
    process(restored, inputs)
    assert hashes(restored) == expected
    new_report = build_report(restored, "2024-04", "DEMO_01", "synthetic")
    assert new_report["report_id"] != report["report_id"]
    assert objects(original_bucket) == inventory and hashes(original) == expected
    assert catalog_hash(original) == original_catalog_hash
    assert checksum(dump) == manifest["database_dump_sha256"]
    result = {
        **{k: v for k, v in manifest.items() if k != "objects"},
        "scope": (
            "quiesced synthetic restore into separate Postgres/MinIO containers on the same host"
            if isolated_target
            else "quiesced synthetic logical restore; separate DBs/buckets on the same local servers"
        ),
        "active_partitions": len(expected),
        "object_count": len(inventory),
        "restore_through_api_verification_seconds": restore_seconds,
        "total_drill_seconds": round(time.monotonic() - started, 3),
        "object_hashes_and_original_reports_equal": True,
        "restored_raw_replay_hashes_equal": True,
        "original_catalog_and_objects_unchanged": True,
        "disaster_recovery_rto_rpo_validated": False,
        "note": "Original dump and artifact bytes preserved; restored catalog S3 bucket references remapped. Historical manifests use the original bucket mapping above. No resources deleted.",
    }
    (output / "evidence.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--isolated-target", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_drill(args.output, args.isolated_target), indent=2))
