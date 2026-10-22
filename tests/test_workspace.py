import uuid

from fastapi.testclient import TestClient
from sqlalchemy import event, select

from solarops.api.app import create_app
from solarops.api.readmodels import fleet_overview, run_history
from solarops.config import CALCULATION_VERSION, Settings
from solarops.storage.postgres import Catalog, active, metrics, put, runs
from tests.test_pipeline import run


def seed_metric(
    catalog,
    day,
    expected,
    valid,
    *,
    plant="PS_001",
    org="demo",
    kind="public",
    version=CALCULATION_VERSION,
    timezone="UTC",
):
    run_id = str(uuid.uuid4())
    key = dict(
        org_id=org,
        plant_id=plant,
        partition_id=day,
        report_timezone=timezone,
        calculation_version=version,
    )
    with catalog.engine.begin() as conn:
        put(
            conn,
            active,
            key,
            {
                "source_objects": [{"source_kind": kind}],
                "metadata": {"nominal_power_kw": 1000, "brazil_federative_unit": "SP"},
            },
            run_id=run_id,
        )
        put(
            conn,
            metrics,
            {"run_id": run_id},
            dict(
                expected_slots=expected,
                observed_slots=expected,
                valid_slots=valid,
                invalid_slots=expected - valid,
                missing_slots=0,
                estimated_energy_kwh=expected,
                source_interpolation_ratio=0.2,
                interpolation_unknown_slots=0,
                review_candidate_count=0,
            ),
        )


def test_fleet_weighting_scope_and_one_query(settings):
    catalog = Catalog(settings)
    seed_metric(catalog, "2024-04-01", 10, 5)
    seed_metric(catalog, "2024-04-02", 90, 90)
    seed_metric(catalog, "2024-04-01", 100, 0, plant="DEMO_01", kind="synthetic")
    seed_metric(catalog, "2024-04-01", 1000, 0, org="other")
    seed_metric(catalog, "2024-04-01", 1000, 0, version="retired")
    seed_metric(catalog, "2024-04-01", 1000, 0, timezone="Asia/Seoul")
    statements = []

    def count(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(catalog.engine, "before_cursor_execute", count)
    try:
        result = fleet_overview(catalog, "2024-04", "public")
    finally:
        event.remove(catalog.engine, "before_cursor_execute", count)
    assert len(statements) == 1 and statements[0].lstrip().startswith("SELECT")
    summary = result["summary"]
    assert summary["plant_count"] == 1 and summary["partition_count"] == 2
    assert summary["valid_coverage_ratio"] == 0.95  # Not (.5 + 1) / 2.
    assert summary["source_interpolation_ratio"] == 0.2
    assert summary["estimated_energy_kwh"] == 100
    assert result["plants"][0]["period_complete"] is False
    assert result["timeline"][2] == {"day": "2024-04-03", "metrics": None}
    assert len(result["timeline"]) == 30
    assert fleet_overview(catalog, "2024-04")["summary"]["plant_count"] == 2


def test_empty_overview_and_api_validation(settings):
    client = TestClient(create_app(settings))
    result = client.get("/api/v1/overview?period=2024-02").json()
    assert result["summary"]["plant_count"] == 0
    assert result["summary"]["valid_coverage_ratio"] is None
    assert len(result["timeline"]) == 29 and all(d["metrics"] is None for d in result["timeline"])
    for query in (
        "period=2024-13",
        "period=foo",
        "period=0000-01",
        "period=2024-01&source_kind=customer",
    ):
        assert client.get("/api/v1/overview?" + query).status_code == 422
    assert client.post("/api/v1/overview?period=2024-04").status_code == 405
    assert client.get("/static/dashboard.js").status_code == 200
    assert client.get("/static/../app.py").status_code == 404


def test_history_latest_first_filters_and_legacy(settings):
    catalog = Catalog(settings)
    records = [
        ("old", "committed", {"kind": "ingest", "finished_at": "2024-01-01T00:00:00+00:00"}),
        ("new", "running", {"kind": "ingest", "started_at": "2024-04-01T00:00:00+00:00"}),
        (
            "failed",
            "failed",
            {
                "kind": "ingest",
                "started_at": "2024-03-01T00:00:00+00:00",
                "finished_at": "2024-03-01T01:00:00+00:00",
            },
        ),
        (
            "partition",
            "failed",
            {"partition_id": "2024-04-01", "started_at": "2024-04-02T00:00:00+00:00"},
        ),
    ]
    with catalog.engine.begin() as conn:
        for run_id, status, payload in records:
            put(
                conn,
                runs,
                {"run_id": run_id},
                dict(payload, plant_id="PS_001"),
                org_id="demo",
                status=status,
            )
        put(
            conn, runs, {"run_id": "other-org"}, {"kind": "ingest"}, org_id="other", status="failed"
        )
    result = run_history(catalog, "batch", limit=1)
    assert result["total"] == 3 and result["items"][0]["run_id"] == "new"
    assert result["status_counts"] == {"committed": 1, "failed": 1, "running": 1}
    assert run_history(catalog, "batch", offset=1, limit=1)["items"][0]["run_id"] == "failed"
    assert run_history(catalog, "batch", status="failed")["total"] == 1
    assert run_history(catalog, "partition")["items"][0]["run_id"] == "partition"
    assert run_history(catalog, plant="UNKNOWN")["total"] == 0


def test_batch_detail_preserves_start_and_links_children(settings, sample):
    result = run(settings, sample, start="2024-04-03", end="2024-04-05")
    client = TestClient(create_app(settings))
    detail = client.get("/api/v1/runs/" + result["batch_id"]).json()
    assert detail["started_at"] <= detail["finished_at"]
    assert detail["elapsed_ms"] >= 0 and detail["source_version"] == "v1"
    assert len(detail["partitions"]) == 2
    assert {p["batch_id"] for p in detail["partitions"]} == {result["batch_id"]}
    assert detail["rows"] == sum(p["rows"] for p in detail["partitions"])
    other = Settings(
        root=settings.root, database_url=settings.database_url, org="other", s3_endpoint=None
    )
    assert (
        TestClient(create_app(other)).get("/api/v1/runs/" + result["batch_id"]).status_code == 404
    )
    assert client.get("/api/v1/runs?status=unknown").status_code == 422
    assert client.get("/api/v1/runs?offset=-1").status_code == 422


def test_failed_batch_keeps_linked_day_evidence(settings, sample):
    import pytest

    with pytest.raises(RuntimeError, match="INJECTED"):
        run(settings, sample, fail_at="during_commit")
    catalog = Catalog(settings)
    batch = run_history(catalog, "batch", status="failed")["items"][0]
    assert batch["error_code"] == "INJECTED_DURING_COMMIT"
    with catalog.engine.connect() as conn:
        child = (
            conn.execute(
                select(runs).where(runs.c.payload["batch_id"].as_string() == batch["run_id"])
            )
            .mappings()
            .one()
        )
    assert child["status"] == "failed"
    assert catalog.snapshot("demo") == []
