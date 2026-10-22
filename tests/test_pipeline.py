import csv
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from solarops.api.app import create_app
from solarops.config import Settings
from solarops.pipeline import ingest
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog, active, put, runs, sources


def run(settings, sample, version="v1", start="2024-04-01", end="2024-04-08", **kwargs):
    return ingest(
        settings,
        sample["metadata"],
        sample["inverter"],
        sample["station"],
        "DEMO_01",
        start,
        end,
        version,
        **kwargs,
    )


def hashes(settings):
    return {
        r["partition_id"]: r["payload"]["logical_content_hash"]
        for r in Catalog(settings).snapshot(settings.org)
    }


def test_three_replays_identical(settings, sample):
    results = [run(settings, sample) for _ in range(3)]
    assert (
        len(
            {
                json.dumps([(r["day"], r["rows"], r["logical_hash"]) for r in result["results"]])
                for result in results
            }
        )
        == 1
    )
    assert len(Catalog(settings).snapshot(settings.org)) == 7
    with Catalog(settings).engine.connect() as c:
        assert len(c.execute(select(sources)).all()) == 3


def test_old_calculation_version_not_double_counted(settings, sample):
    run(settings, sample)
    catalog = Catalog(settings)
    row = catalog.snapshot(settings.org)[0]
    key = {
        field: row[field]
        for field in (
            "org_id",
            "plant_id",
            "partition_id",
            "report_timezone",
            "calculation_version",
        )
    }
    key["calculation_version"] = "retired-v0"
    with catalog.engine.begin() as conn:
        put(conn, active, key, row["payload"], run_id=row["run_id"])
    assert len(catalog.snapshot(settings.org)) == 7


@pytest.mark.parametrize("failure", ["before_commit", "during_commit"])
def test_failure_keeps_published_partition(settings, sample, failure):
    run(settings, sample)
    before = hashes(settings)
    with pytest.raises(RuntimeError, match="INJECTED"):
        run(settings, sample, fail_at=failure)
    assert hashes(settings) == before
    with Catalog(settings).engine.connect() as c:
        assert c.execute(select(runs).where(runs.c.status == "failed")).first()


def test_targeted_replay_preserves_other_days(settings, sample):
    run(settings, sample)
    before = {r["partition_id"]: r["run_id"] for r in Catalog(settings).snapshot(settings.org)}
    run(settings, sample, start="2024-04-03", end="2024-04-04")
    after = {r["partition_id"]: r["run_id"] for r in Catalog(settings).snapshot(settings.org)}
    assert [day for day in before if before[day] != after[day]] == ["2024-04-03"]


def test_changed_input_requires_explicit_version(settings, sample):
    run(settings, sample)
    with sample["inverter"].open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["2024-04-01T00:00:00Z", "DEMO_01", 1, 999, "false", 3])
    with pytest.raises(ValueError, match="SOURCE_VERSION_CONFLICT"):
        run(settings, sample)
    before = hashes(settings)
    with pytest.raises(ValueError, match="DUPLICATE_CONFLICT"):
        run(settings, sample, version="v2")
    assert hashes(settings) == before


def test_late_arrival_new_version(settings, sample):
    run(settings, sample)
    old = Catalog(settings).snapshot(settings.org, "2024-04-02", "2024-04-03")[0]["metric"]
    with sample["inverter"].open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["2024-04-02T11:00:00Z", "DEMO_01", 2, 5000, "false", 3])
    run(settings, sample, version="v2", start="2024-04-02", end="2024-04-03")
    new = Catalog(settings).snapshot(settings.org, "2024-04-02", "2024-04-03")[0]["metric"]
    assert new["missing_slots"] == old["missing_slots"] - 1
    assert new["estimated_energy_kwh"] == old["estimated_energy_kwh"] + 1.25


def test_org_isolation(settings, sample):
    run(settings, sample)
    other = Settings(
        root=settings.root, database_url=settings.database_url, org="other", s3_endpoint=None
    )
    assert Catalog(other).snapshot("other") == []
    run(other, sample)
    with Catalog(settings).engine.connect() as c:
        assert len(c.execute(select(sources)).all()) == 6
    assert (
        TestClient(create_app(other)).get("/api/v1/plants").json()["items"][0]["plant_id"]
        == "DEMO_01"
    )


def test_report_api_and_lineage(settings, sample):
    run(settings, sample)
    result = build_report(settings, "2024-04")
    assert result["status"] == "partial_period"
    client = TestClient(create_app(settings))
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/plants?limit=0").status_code == 422
    assert client.post("/api/v1/plants").status_code == 405
    assert client.get("/api/v1/plants/DEMO_01/metrics?limit=2").json()["total"] == 7
    assert len(client.get("/api/v1/plants/DEMO_01/series?day=2024-04-01").json()["items"]) == 96
    path = "/reports/" + result["report_id"] + "/"
    html = client.get(path + "report.html")
    assert html.status_code == 200 and "부분 기간" in html.text and "synthetic" in html.text
    assert client.get(path + "secret.env").status_code == 404
    other = Settings(
        root=settings.root, database_url=settings.database_url, org="other", s3_endpoint=None
    )
    assert TestClient(create_app(other)).get(path + "manifest.json").status_code == 404


def test_unknown_plant_and_malformed_timestamp_block(settings, sample):
    text = sample["inverter"].read_text(encoding="utf-8")
    sample["inverter"].write_text(text.replace("DEMO_01", "UNKNOWN"), encoding="utf-8")
    with pytest.raises(ValueError, match="UNKNOWN_PLANT"):
        run(settings, sample)
