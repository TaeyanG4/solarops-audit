import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from sqlalchemy import event, select

from solarops import pipeline
from solarops.acquisition.brpvgen import checksum
from solarops.fixtures import generate
from solarops.reports import render
from solarops.storage import minio
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, plants, reports
from tests.test_pipeline import run


@pytest.mark.parametrize("mode", ["absent", "existing", "duplicate"])
def test_overlapping_batches_cannot_replace_new_publication(
    settings, sample, tmp_path, monkeypatch, mode
):
    if mode == "existing":
        run(settings, sample, version="baseline", end="2024-04-04")
    other = generate(tmp_path / "new-input")
    new_version = "v1" if mode == "duplicate" else "v2"
    if mode != "duplicate":
        other["metadata"].write_text("id,nominal_power_mw\nDEMO_01,0.03\n", encoding="utf-8")
    started, release = Event(), Event()
    original = pipeline.publish_day

    def delayed(*args, **kwargs):
        if args[4] == "2024-04-02" and not started.is_set():
            started.set()
            assert release.wait(30)
        return original(*args, **kwargs)

    monkeypatch.setattr(pipeline, "publish_day", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        older = pool.submit(run, settings, sample, end="2024-04-03")
        try:
            assert started.wait(30)
            newer = run(settings, other, version=new_version, start="2024-04-02", end="2024-04-04")
        finally:
            release.set()
        with pytest.raises(ValueError, match="PUBLICATION_CONFLICT"):
            older.result(timeout=30)
    catalog = Catalog(settings)
    snapshot = catalog.snapshot(settings.org)
    assert [r["run_id"] for r in snapshot[1:]] == [r["run_id"] for r in newer["results"]]
    assert snapshot[0]["payload"]["active_source_version"] == "v1"
    with catalog.engine.connect() as conn:
        meta = conn.execute(
            select(plants.c.payload).where(plants.c.org_id == settings.org)
        ).scalar_one()
        assert meta["nominal_power_kw"] == (20 if mode == "duplicate" else 30)
    # Retrying the winning input is deterministic and preserves other dates.
    retried = run(settings, other, version=new_version, start="2024-04-02", end="2024-04-04")
    assert [r["logical_hash"] for r in retried["results"]] == [
        r["logical_hash"] for r in newer["results"]
    ]
    assert catalog.snapshot(settings.org)[0]["run_id"] == snapshot[0]["run_id"]


def test_historical_restore_is_explicit_and_audited(settings, sample):
    first = run(settings, sample, end="2024-04-02")
    newer = run(settings, sample, version="v2", end="2024-04-02")
    with pytest.raises(ValueError, match="HISTORICAL_RESTORE_REQUIRES_FLAG"):
        run(settings, sample, end="2024-04-02")
    restored = run(settings, sample, end="2024-04-02", restore=True)
    assert restored["results"][0]["logical_hash"] == first["results"][0]["logical_hash"]
    manifest = Catalog(settings).snapshot(settings.org)[0]["payload"]
    assert manifest["restore_requested"] is True
    assert manifest["previous_run_id"] == newer["results"][0]["run_id"]


def test_raw_copy_is_published_only_when_complete(settings, sample, monkeypatch):
    store = ObjectStore(settings)
    source = sample["inverter"]
    digest = checksum(source)
    copying, release = Event(), Event()
    original = minio.shutil.copyfileobj

    def delayed_copy(src, out, *args):
        if not copying.is_set():
            out.write(src.read(10))
            out.flush()
            copying.set()
            assert release.wait(10)
        original(src, out, *args)

    monkeypatch.setattr(minio.shutil, "copyfileobj", delayed_copy)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(store.raw, source, settings.org, digest)
        try:
            assert copying.wait(10)
            second = pool.submit(store.raw, source, settings.org, digest).result(timeout=10)
            assert checksum(store.raw_path(settings.org, digest, source.name)) == digest
        finally:
            release.set()
        assert first.result(timeout=10) == second


def test_changed_source_during_capture_never_publishes_bad_raw(settings, sample):
    store = ObjectStore(settings)
    path = sample["inverter"]
    digest = checksum(path)
    path.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum") as error:
        store.raw(path, settings.org, digest)
    from solarops.contracts.brpvgen import failure_code

    assert failure_code(error.value) == "RAW_OBJECT_CHECKSUM_MISMATCH"
    assert not store.raw_path(settings.org, digest, path.name).exists()


@pytest.mark.parametrize("failure", ["upload", "catalog"])
def test_failed_report_keeps_previous_publication(settings, sample, monkeypatch, failure):
    run(settings, sample)
    previous = render.build_report(settings, "2024-04")
    if failure == "upload":
        original = ObjectStore.upload

        def fail_upload(store, path, key):
            if path.name == "metrics.csv":
                raise RuntimeError("injected upload")
            return original(store, path, key)

        monkeypatch.setattr(ObjectStore, "upload", fail_upload)
    else:
        original = render.Catalog

        def failing_catalog(config):
            catalog = original(config)

            def fail_active(conn, cursor, statement, params, context, many):
                if statement.startswith("INSERT INTO active_report_manifest"):
                    raise RuntimeError("injected catalog")

            event.listen(catalog.engine, "before_cursor_execute", fail_active)
            return catalog

        monkeypatch.setattr(render, "Catalog", failing_catalog)
    with pytest.raises(RuntimeError, match="injected"):
        render.build_report(settings, "2024-04")
    with Catalog(settings).engine.connect() as conn:
        assert (
            conn.execute(
                select(active_reports.c.report_run_id).where(
                    active_reports.c.org_id == settings.org
                )
            ).scalar_one()
            == previous["report_id"]
        )
        assert conn.execute(
            select(reports.c.report_run_id).where(reports.c.org_id == settings.org)
        ).scalars().all() == [previous["report_id"]]


def test_slow_old_report_does_not_replace_newer_snapshot(settings, sample, monkeypatch):
    run(settings, sample)
    started, release = Event(), Event()
    original = render.env.get_template

    def delayed_template(*args, **kwargs):
        if not started.is_set():
            started.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(render.env, "get_template", delayed_template)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(render.build_report, settings, "2024-04")
        try:
            assert started.wait(10)
            run(settings, sample)
            newer = render.build_report(settings, "2024-04")
        finally:
            release.set()
        older = first.result(timeout=10)
    assert older["source_manifest_hash"] != newer["source_manifest_hash"]
    with Catalog(settings).engine.connect() as conn:
        assert (
            conn.execute(
                select(active_reports.c.report_run_id).where(
                    active_reports.c.org_id == settings.org
                )
            ).scalar_one()
            == newer["report_id"]
        )
        assert len(conn.execute(select(reports).where(reports.c.org_id == settings.org)).all()) == 2
    # Both historical files remain independently usable.
    for report in (older, newer):
        assert (
            json.loads(
                (Path(report["local_directory"]) / "manifest.json").read_text(encoding="utf-8")
            )["report_id"]
            == report["report_id"]
        )


def test_ons_incremental_correction_withdrawal_and_atomic_cursor(settings, tmp_path):
    import uuid
    from dataclasses import replace

    from fastapi.testclient import TestClient

    from solarops.acquisition.ons import cursor, publish, status
    from solarops.api.app import create_app
    from solarops.storage.minio import ObjectStore
    from solarops.storage.postgres import Catalog
    from tests.test_contracts import ons_csv

    catalog, store = Catalog(settings), ObjectStore(settings)
    p = tmp_path / "ons.csv"
    values = [(1, 0, "1", "TIPO II-B", "A"), (2, 0, "2", "TIPO II-B", "A")]

    def apply(rows, expected, fail=None):
        ons_csv(p, rows)
        return publish(catalog, store, p, "2026-10", expected, str(uuid.uuid4()), {}, fail)

    first = apply(values, None)
    identical = apply(values, first)
    assert identical["changed_days"] == []
    before = status(catalog, "2026-10")["partitions"]
    changed = [(1, 0, "3", "TIPO II-B", "A"), values[1], (3, 0, "4", "TIPO II-B", "A")]
    with pytest.raises(RuntimeError, match="PUBLICATION_FAILURE"):
        apply(changed, identical, "during_commit")
    assert cursor(catalog, "2026-10") == identical
    assert status(catalog, "2026-10")["partitions"] == before
    correction = apply(changed, identical)
    assert correction["changed_days"] == ["2026-10-01", "2026-10-03"]
    after = status(catalog, "2026-10")["partitions"]
    assert before[1] == after[1]
    with pytest.raises(ValueError, match="CURSOR_CONFLICT"):
        apply(values, identical)
    assert cursor(catalog, "2026-10") == correction
    withdrawn = apply([changed[0], changed[2]], correction)
    assert withdrawn["changed_days"] == ["2026-10-02"]
    assert status(catalog, "2026-10")["partitions"][1]["state"] == "withdrawn"
    client = TestClient(create_app(settings))
    result = client.get("/api/v1/sources/ons/days/2026-10-01?limit=1").json()
    assert result["items"][0]["generation_mwmed"] == 3
    assert result["items"][0]["ts_utc"] is None
    assert client.get("/api/v1/sources/ons?period=2026-13").status_code == 422
    other = replace(settings, org=settings.org + "-other")
    other_status = status(Catalog(other), "2026-10")
    assert other_status["partitions"] == []
    assert other_status["last_success"] is None
    assert other_status["available_periods"] == []
    assert (
        TestClient(create_app(other)).get("/api/v1/sources/ons/days/2026-10-01").status_code == 404
    )
    assert Catalog(settings).snapshot(settings.org) == []


def test_ons_conditional_download_and_failure_preserve_success(settings, tmp_path, monkeypatch):
    import json

    from solarops.acquisition import ons
    from tests.test_contracts import ons_csv

    sample = ons_csv(tmp_path / "sample.csv", [(1, 0, "1", "TIPO II-B", "A")]).read_bytes()
    calls = []

    def download(url, path, etag=None, **kwargs):
        if url == ons.API:
            path.write_text(
                json.dumps(
                    {
                        "success": True,
                        "result": {
                            "license_id": "cc-by",
                            "resources": [{"url": ons.source_url("2026-10")}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            return {}
        calls.append(etag)
        if etag:
            return {"not_modified": True, "etag": etag}
        path.write_bytes(sample)
        return {"not_modified": False, "etag": '"v1"'}

    monkeypatch.setattr(ons, "download", download)
    first = ons.sync_month(settings, "2026-10")
    second = ons.sync_month(settings, "2026-10")
    assert calls == [None, '"v1"'] and second["changed_days"] == []
    assert first["raw_sha256"] == second["raw_sha256"]

    def failure(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(ons, "download", failure)
    with pytest.raises(OSError):
        ons.sync_month(settings, "2026-10")
    catalog = ons.Catalog(settings)
    assert ons.cursor(catalog, "2026-10") == second
    assert ons.status(catalog, "2026-10")["recent_attempts"][0]["status"] == "failed"
    from fastapi.testclient import TestClient

    from solarops.api.app import create_app

    client = TestClient(create_app(settings))
    result = client.get("/api/v1/sources/ons?period=2026-10").json()
    assert result["last_success"] == second
    assert result["recent_attempts"][0]["status"] == "failed"
    assert result["available_periods"] == ["2026-10"]
    assert result["storage"]["scheduler_status"] == "not_observed"
    assert "database_url" not in result["storage"]
    # Domain causes remain distinct, while arbitrary exception details stay private.
    from urllib.error import HTTPError, URLError

    failures = (
        (ValueError("ONS_SCHEMA_CHANGED"), "ONS_SCHEMA_CHANGED"),
        (
            ValueError("RAW_OBJECT_CHECKSUM_MISMATCH: private detail"),
            "RAW_OBJECT_CHECKSUM_MISMATCH",
        ),
        (ValueError("ONS_SOURCE_CONTRACT_CHANGED"), "ONS_SOURCE_CONTRACT_CHANGED"),
        (ValueError("ONS_CURSOR_CONFLICT: internal detail"), "ONS_CURSOR_CONFLICT"),
        (TimeoutError("private endpoint"), "ONS_TIMEOUT"),
        (HTTPError("https://private.invalid", 503, "private detail", {}, None), "ONS_HTTP_503"),
        (URLError("private endpoint"), "ONS_NETWORK_ERROR"),
        (OSError("private path"), "ONS_IO_ERROR"),
        (ValueError("private connection string"), "ONS_UNEXPECTED_ERROR"),
    )
    for exception, expected_code in failures:

        def fail(*args, _exc=exception, **kwargs):
            raise _exc

        monkeypatch.setattr(ons, "download", fail)
        with pytest.raises(type(exception)):
            ons.sync_month(settings, "2026-10")
        result = client.get("/api/v1/sources/ons?period=2026-10").json()
        assert result["recent_attempts"][0]["error_code"] == expected_code
        assert result["last_success"] == second
        assert "private" not in json.dumps(result["recent_attempts"])
    # Last success comes from the cursor even when >20 later failures hide it.
    from solarops.storage.postgres import collection_runs, put

    with catalog.engine.begin() as conn:
        for i in range(21):
            put(
                conn,
                collection_runs,
                {"org_id": settings.org, "run_id": f"failure-{i}"},
                {
                    "source_id": ons.SOURCE,
                    "period": "2026-10",
                    "status": "failed",
                    "finished_at": f"2099-10-23T00:00:{i:02d}+00:00",
                },
            )
    result = client.get("/api/v1/sources/ons?period=2026-10").json()
    assert len(result["recent_attempts"]) == 20
    assert all(r["status"] == "failed" for r in result["recent_attempts"])
    assert result["last_success"] == second
    empty = client.get("/api/v1/sources/ons?period=2026-09").json()
    assert empty["last_success"] is None and empty["partitions"] == []
    # Secondary DB errors must not mask the download/validation error.
    original_put = ons.put

    def unavailable_failure_record(conn, relation, key, payload, **kwargs):
        if relation is collection_runs and payload.get("status") == "failed":
            raise RuntimeError("private-secondary-database-error")
        return original_put(conn, relation, key, payload, **kwargs)

    monkeypatch.setattr(ons, "download", failure)
    monkeypatch.setattr(ons, "put", unavailable_failure_record)
    with pytest.raises(OSError, match="offline"):
        ons.sync_month(settings, "2026-10")
    assert ons.cursor(catalog, "2026-10") == second
