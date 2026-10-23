import csv
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from sqlalchemy import event, select, text, update
from sqlalchemy.exc import OperationalError

from solarops.api.app import create_app
from solarops.contracts.brpvgen import failure_code, read_metadata
from solarops.fixtures import generate
from solarops.reports.render import build_report
from solarops.storage import minio, postgres
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active, reports, versions
from tests.test_pipeline import hashes, run


@pytest.mark.parametrize(
    "contents",
    [
        "id,nominal_power_mw,nominal_power_mw\nDEMO_01,0.02,900\n",
        "id,nominal_power_mw\nDEMO_01,0.02,unexpected\n",
        "id,nominal_power_mw,label\nDEMO_01,0.02\n",
    ],
)
def test_metadata_ambiguous_columns_rejected(tmp_path, contents):
    path = tmp_path / "ambiguous.csv"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match="Metadata contract"):
        read_metadata(path)


def test_processing_reads_captured_raw_not_mutated_input(settings, sample, monkeypatch):
    run(settings, sample)
    expected = hashes(settings)
    original = ObjectStore.raw

    def changing_input(store, path, org, digest):
        uri = original(store, path, org, digest)
        if path == sample["inverter"]:
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                row["total_active_power_w"] = "0"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=rows[0])
                writer.writeheader()
                writer.writerows(rows)
        return uri

    monkeypatch.setattr(ObjectStore, "raw", changing_input)
    run(settings, sample)
    assert hashes(settings) == expected


def test_readiness_does_not_create_missing_bucket(settings, monkeypatch):
    Catalog(settings).engine.dispose()

    class MissingBucket:
        created = False

        def head_bucket(self, **kwargs):
            if not self.created:
                raise ClientError({"Error": {"Code": "NoSuchBucket"}}, "HeadBucket")

        def create_bucket(self, **kwargs):
            self.created = True

    fake = MissingBucket()
    monkeypatch.setattr(minio.boto3, "client", lambda *a, **k: fake)
    monkeypatch.setenv("SOLAROPS_S3_ACCESS_KEY", "synthetic")
    monkeypatch.setenv("SOLAROPS_S3_SECRET_KEY", "synthetic")
    client = TestClient(create_app(replace(settings, s3_endpoint="http://127.0.0.1:1")))
    assert client.get("/ready").status_code == 503
    assert not fake.created


def test_missing_report_artifact_is_a_controlled_response(settings, sample):
    run(settings, sample)
    report = build_report(settings, "2024-04")
    payload = dict(report, artifacts={"report.html": str(settings.root / "missing.html")})
    with Catalog(settings).engine.begin() as conn:
        conn.execute(update(reports).values(payload=payload))
    client = TestClient(create_app(settings), raise_server_exceptions=False)
    response = client.get(f"/reports/{report['report_id']}/report.html")
    assert response.status_code == 404
    assert "missing.html" not in response.text
    freshness = client.get(f"/api/v1/reports/{report['report_id']}/freshness")
    assert freshness.status_code == 200 and freshness.json()["status"] == "unavailable"


def test_read_api_does_not_initialize_missing_catalog(settings):
    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        response = client.get("/api/v1/plants")
        assert response.status_code == 503
        assert str(settings.root) not in response.text
    assert not (settings.root.parent / "catalog.db").exists()
    assert not settings.root.exists()


def test_read_only_catalog_rejects_writes_and_missing_schema(settings):
    catalog = Catalog(settings)
    with catalog.engine.begin() as conn:
        conn.execute(text("ALTER TABLE report_run RENAME TO preserved_report_run"))
    catalog.engine.dispose()
    read_catalog = Catalog(settings, read_only=True)
    with read_catalog.engine.begin() as conn, pytest.raises(OperationalError):
        conn.execute(text("CREATE TABLE forbidden (id INTEGER)"))
    read_catalog.engine.dispose()
    with TestClient(create_app(settings)) as client:
        assert client.get("/ready").status_code == 503


def test_series_and_report_integrity_and_legacy_compatibility(settings, sample):
    run(settings, sample)
    report = build_report(settings, "2024-04")
    catalog = Catalog(settings)
    partition = catalog.snapshot(settings.org)[0]
    series_path = Path(partition["payload"]["series_uri"])
    report_path = Path(report["artifacts"]["report.html"])
    with TestClient(create_app(settings)) as client:
        series_url = f"/api/v1/plants/DEMO_01/series?day={partition['partition_id']}"
        report_url = f"/reports/{report['report_id']}/report.html"
        assert client.get(series_url).status_code == 200
        assert client.get(report_url).status_code == 200
        # Whitespace preserves valid JSON/HTML but must still fail byte integrity.
        series_path.write_bytes(series_path.read_bytes() + b" ")
        report_path.write_bytes(report_path.read_bytes() + b" ")
        for url in (series_url, report_url):
            response = client.get(url)
            assert response.status_code == 503
            assert response.json()["detail"] == "Artifact integrity check failed"
        legacy = dict(partition["payload"])
        legacy.pop("series_sha256")
        old_report = dict(report)
        old_report.pop("artifact_sha256")
        with catalog.engine.begin() as conn:
            conn.execute(
                update(active).where(active.c.run_id == partition["run_id"]).values(payload=legacy)
            )
            conn.execute(update(reports).values(payload=old_report))
        assert client.get(series_url).status_code == 200
        assert client.get(report_url).status_code == 200
        series_path.write_text("{broken", encoding="utf-8")
        assert client.get(series_url).status_code == 503
    # Metrics have always carried the unknown-interpolation count; a row without it
    # is outside the contract and must not become an implicit 0% / known value.
    tampered = dict(partition["metric"])
    tampered.pop("interpolation_unknown_slots")
    with catalog.engine.begin() as conn:
        conn.execute(
            update(postgres.metrics)
            .where(postgres.metrics.c.run_id == partition["run_id"])
            .values(payload=tampered)
        )
    report_dirs = set((settings.root / "reports" / settings.org).iterdir())
    with pytest.raises(ValueError, match="METRIC_CONTRACT_MISMATCH") as failure:
        build_report(settings, "2024-04")
    assert failure_code(failure.value) == "METRIC_CONTRACT_MISMATCH"
    assert set((settings.root / "reports" / settings.org).iterdir()) == report_dirs


def test_concurrent_different_inputs_cannot_claim_same_version(settings, tmp_path, monkeypatch):
    Catalog(settings).engine.dispose()
    barrier = Barrier(2)
    create_engine = postgres.create_engine

    def instrumented(*args, **kwargs):
        engine = create_engine(*args, **kwargs)

        def synchronize_unprotected_read(conn, cursor, statement, params, context, many):
            # Force the actual SQLite read-then-write race; a write transaction is protected.
            if (
                statement.startswith("SELECT source_version.")
                and "WHERE source_version." in statement
                and not conn.connection.driver_connection.in_transaction
            ):
                barrier.wait(timeout=10)

        event.listen(engine, "after_cursor_execute", synchronize_unprotected_read)
        return engine

    monkeypatch.setattr(postgres, "create_engine", instrumented)
    inputs = [generate(tmp_path / f"input-{n}") for n in range(2)]
    inputs[1]["metadata"].write_text("id,nominal_power_mw\nDEMO_01,0.03\n", encoding="utf-8")

    def attempt(n):
        try:
            run(replace(settings, root=tmp_path / f"worker-{n}"), inputs[n], end="2024-04-02")
            return "committed"
        except ValueError as exc:
            assert str(exc).startswith("SOURCE_VERSION_CONFLICT")
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, range(2)))
    assert sorted(outcomes) == ["committed", "conflict"]
    with Catalog(settings).engine.connect() as conn:
        version = conn.execute(select(versions.c.payload)).scalar_one()
    active = Catalog(settings).snapshot(settings.org)[0]["payload"]
    assert [s["sha256"] for s in version["source_objects"]] == [
        s["sha256"] for s in active["source_objects"]
    ]
