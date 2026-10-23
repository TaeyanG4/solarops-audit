from datetime import UTC, datetime

import pytest
from sqlalchemy import event, select

from solarops import diagnostics
from solarops.diagnostics import inspect_runs
from solarops.storage.postgres import Catalog, active, put, runs


def test_unfinished_runs_are_evidence_not_auto_failed(settings, monkeypatch):
    catalog = Catalog(settings)
    at = datetime(2024, 4, 1, 12, tzinfo=UTC)
    entries = [
        ("old", "demo", "running", {"kind": "ingest", "started_at": "2024-04-01T10:00:00+00:00"}),
        ("recent", "demo", "running", {"started_at": "2024-04-01T11:59:00+00:00"}),
        ("missing", "demo", "validated", {}),
        ("invalid", "demo", "running", {"started_at": "2024-01-01"}),
        ("future", "demo", "running", {"started_at": "2024-04-02T12:00:00+00:00"}),
        ("other", "other", "running", {"started_at": "2024-01-01T00:00:00+00:00"}),
        ("child", "demo", "committed", {"batch_id": "old"}),
        ("foreign-child", "other", "failed", {"batch_id": "old"}),
    ]
    with catalog.engine.begin() as conn:
        for run_id, org, status, payload in entries:
            put(conn, runs, {"run_id": run_id}, payload, org_id=org, status=status)
        for run_id, org in (("child", "demo"), ("missing", "demo"), ("foreign-child", "other")):
            put(
                conn,
                active,
                {
                    "org_id": org,
                    "plant_id": run_id,
                    "partition_id": "2024-04-01",
                    "report_timezone": "UTC",
                    "calculation_version": "test",
                },
                {},
                run_id=run_id,
            )
    with catalog.engine.connect() as conn:
        before = conn.execute(select(runs)).all()
    # Record every executed statement: diagnostics must not issue schema, status or data writes.
    statements = []
    event.listen(
        catalog.engine,
        "before_cursor_execute",
        lambda c, cur, stmt, p, ctx, many: statements.append(stmt),
    )
    monkeypatch.setattr(diagnostics, "create_engine", lambda *a, **k: catalog.engine)
    result = inspect_runs(settings, at=at)
    assert result["total_unfinished"] == 5 and not result["has_more"]
    items = {r["run_id"]: r for r in result["items"]}
    assert items["old"]["needs_review"] and items["old"]["age_seconds"] == 7200
    assert items["old"]["active_child_partition_count"] == 1
    assert items["old"]["child_status_counts"] == {"committed": 1}
    assert not items["recent"]["needs_review"]
    assert items["missing"]["reason"] == items["invalid"]["reason"] == "start_time_unavailable"
    assert items["missing"]["active_partition_count"] == 1
    assert items["future"]["reason"] == "clock_skew"
    page = inspect_runs(settings, limit=2, offset=2, at=at)
    assert page["items"] == result["items"][2:4] and page["has_more"]
    detail = inspect_runs(settings, at=at, run_id="old")
    assert detail["item"] == items["old"]
    assert not detail["active_result_lookup_complete"]
    assert inspect_runs(settings, at=at, run_id="child")["item"]["reason"] == "finished"
    assert inspect_runs(settings, at=at, run_id="other")["item"] is None
    with catalog.engine.connect() as conn:
        assert conn.execute(select(runs)).all() == before
    assert all(stmt.lstrip().upper().startswith("SELECT") for stmt in statements)


@pytest.mark.parametrize(
    "kwargs", [{"limit": 0}, {"limit": 501}, {"offset": -1}, {"older_than_minutes": 0}]
)
def test_invalid_diagnostic_bounds_are_rejected(settings, kwargs):
    with pytest.raises(ValueError):
        inspect_runs(settings, **kwargs)


def test_absent_database_is_not_created(settings):
    from pathlib import Path

    from sqlalchemy.engine import make_url

    database = Path(make_url(settings.database_url).database)
    assert not database.exists()
    with pytest.raises(ValueError, match="existing database"):
        inspect_runs(settings)
    assert not database.exists()


def test_existing_sqlite_is_opened_read_only(settings):
    catalog = Catalog(settings)
    catalog.engine.dispose()
    assert inspect_runs(settings)["total_unfinished"] == 0


def test_failed_attempt_links_retry_active_result_and_release(settings, sample, monkeypatch):
    from tests.test_pipeline import run

    for name, value in {
        "DAG_ID": "daily",
        "DAG_RUN_ID": "manual__test",
        "TASK_ID": "publish",
        "TASK_ATTEMPT": "1",
        "POD_UID": "failed-pod",
    }.items():
        monkeypatch.setenv("SOLAROPS_" + name, value)
    with pytest.raises(RuntimeError, match="INJECTED"):
        run(settings, sample, end="2024-04-02", fail_at="during_commit")
    with Catalog(settings).engine.connect() as conn:
        failed = conn.execute(
            select(runs.c.run_id).where(
                runs.c.org_id == settings.org, runs.c.payload["kind"].as_string() == "partition"
            )
        ).scalar_one()
    monkeypatch.setenv("SOLAROPS_TASK_ATTEMPT", "2")
    monkeypatch.setenv("SOLAROPS_POD_UID", "retry-pod")
    retry = run(settings, sample, end="2024-04-02")
    detail = inspect_runs(settings, run_id=failed)
    item = detail["item"]
    assert item["stage"] == "publishing" and item["rows"] > 0
    assert item["error_code"] == "INJECTED_DURING_COMMIT"
    assert item["execution"]["pod_uid"] == "failed-pod"
    assert item["release"]["release_id"] and item["release"]["git_revision"]
    assert detail["active_result"]["run_id"] == retry["results"][0]["run_id"]
    assert detail["related_attempts"][0]["run_id"] == retry["results"][0]["run_id"]
    assert detail["related_attempts"][0]["execution"]["task_attempt"] == "2"
