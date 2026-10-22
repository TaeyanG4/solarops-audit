import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from sqlalchemy import event, select

from solarops.acquisition.brpvgen import checksum
from solarops.reports import render
from solarops.storage import minio
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, reports
from tests.test_pipeline import run


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
