import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from solarops.api.app import create_app
from solarops.config import Settings
from solarops.fixtures import generate
from solarops.reports.render import build_report
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog
from tests.test_pipeline import run
from tests.test_publication_boundaries import (
    test_failed_report_keeps_previous_publication as check_failed_report,
)
from tests.test_publication_boundaries import (
    test_slow_old_report_does_not_replace_newer_snapshot as check_report_order,
)


@pytest.mark.services
@pytest.mark.skipif(
    not os.getenv("SOLAROPS_TEST_SERVICES"), reason="Explicit Postgres/MinIO integration opt-in"
)
def test_postgres_minio_transaction(sample, tmp_path):
    settings = Settings(root=tmp_path, org="test-" + uuid.uuid4().hex[:12])
    first = run(settings, sample)
    with pytest.raises(RuntimeError):
        run(settings, sample, fail_at="during_commit")
    second = run(settings, sample)
    assert [r["logical_hash"] for r in first["results"]] == [
        r["logical_hash"] for r in second["results"]
    ]
    snapshot = Catalog(settings).snapshot(settings.org)
    store = ObjectStore(settings)
    uri = snapshot[0]["payload"]["source_objects"][0]["raw_uri"]
    bucket, key = uri[5:].split("/", 1)
    assert (
        store.client.head_object(Bucket=bucket, Key=key)["ContentLength"]
        == Path(sample["metadata"]).stat().st_size
    )
    client = TestClient(create_app(settings))
    overview = client.get("/api/v1/overview?period=2024-04&source_kind=synthetic").json()
    assert overview["summary"]["partition_count"] == 7
    assert overview["summary"]["plant_count"] == 1
    history = client.get("/api/v1/runs?level=batch&status=failed").json()
    assert history["total"] == 1 and history["status_counts"]["committed"] == 2
    detail = client.get("/api/v1/runs/" + second["batch_id"]).json()
    assert len(detail["partitions"]) == 7
    read_catalog = Catalog(settings, read_only=True)
    with read_catalog.engine.begin() as conn:
        assert conn.execute(text("SHOW transaction_read_only")).scalar_one() == "on"
        with pytest.raises(DBAPIError):
            conn.execute(text("UPDATE dim_plant SET payload = payload WHERE 1 = 0"))
    read_catalog.engine.dispose()
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/plants/DEMO_01/series?day=2024-04-01").status_code == 200
    report = build_report(settings, "2024-04", "DEMO_01", "synthetic")
    freshness = f"/api/v1/reports/{report['report_id']}/freshness"
    artifact = f"/reports/{report['report_id']}/manifest.json"
    original_report = client.get(artifact).content
    assert client.get(freshness).json()["status"] == "unchanged"
    run(settings, sample, start="2024-04-01", end="2024-04-02")
    assert client.get(freshness).json()["status"] == "changed"
    assert client.get(artifact).content == original_report


@pytest.mark.services
@pytest.mark.skipif(not os.getenv("SOLAROPS_TEST_SERVICES"), reason="Explicit service opt-in")
def test_postgres_concurrent_version_claim(tmp_path):
    settings = Settings(root=tmp_path / "catalog", org="test-" + uuid.uuid4().hex[:12])
    Catalog(settings).engine.dispose()
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
        assert sorted(pool.map(attempt, range(2))) == ["committed", "conflict"]
    assert len(Catalog(settings).snapshot(settings.org)) == 1


@pytest.mark.services
@pytest.mark.skipif(not os.getenv("SOLAROPS_TEST_SERVICES"), reason="Explicit service opt-in")
@pytest.mark.parametrize("boundary", ["ordering", "upload", "catalog"])
def test_postgres_report_publication(tmp_path, sample, monkeypatch, boundary):
    settings = Settings(root=tmp_path, org="test-" + uuid.uuid4().hex[:12])
    if boundary == "ordering":
        check_report_order(settings, sample, monkeypatch)
    else:
        check_failed_report(settings, sample, monkeypatch, boundary)
