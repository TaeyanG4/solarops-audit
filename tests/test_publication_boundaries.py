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
    with pytest.raises(ValueError, match="checksum"):
        store.raw(path, settings.org, digest)
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
