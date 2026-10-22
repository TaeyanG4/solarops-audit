import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from solarops.api.app import create_app
from solarops.config import Settings
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog, active_reports
from tests.test_pipeline import run


@pytest.mark.parametrize(
    "query",
    [
        "from=foo",
        "from=2024-02-30",
        "from=20240401",
        "from=2024-W14-1",
        "from=2024-04-02&to=2024-04-01",
        "from=2024-04-01&to=2024-04-01",
        "to=0000-01-01",
        "to=2024-13-01",
    ],
)
def test_invalid_metric_range_returns_422(settings, query):
    assert (
        TestClient(create_app(settings)).get("/api/v1/plants/DEMO_01/metrics?" + query).status_code
        == 422
    )


@pytest.mark.parametrize("day", ["2024-02-30", "20240401", "2024-W14-1", "9999-12-31"])
def test_invalid_series_day_returns_422(settings, day):
    assert (
        TestClient(create_app(settings)).get("/api/v1/plants/DEMO_01/series?day=" + day).status_code
        == 422
    )


@pytest.mark.parametrize("endpoint", ["metrics", "issues", "series?day=2024-04-01"])
def test_plant_identifier_validation_is_consistent(settings, endpoint):
    client = TestClient(create_app(settings))
    for plant in ("invalid!", "x" * 81):
        assert client.get(f"/api/v1/plants/{plant}/{endpoint}").status_code == 422
    assert client.get(f"/api/v1/plants/UNKNOWN/{endpoint}").json()["items"] == []


def test_valid_range_keeps_exclusive_end(settings, sample):
    run(settings, sample)
    client = TestClient(create_app(settings))
    result = client.get("/api/v1/plants/DEMO_01/metrics?from=2024-04-02&to=2024-04-03").json()
    assert result["total"] == 1
    assert result["items"][0]["local_date"] == "2024-04-02"
    assert client.get("/api/v1/plants/DEMO_01/series?day=2024-02-29").json()["items"] == []


def test_report_source_filter_uses_lineage_including_legacy(settings, sample):
    run(settings, sample)
    # Generic scope 'all' used to disappear from both source-specific report views.
    report = build_report(settings, "2024-04")
    assert report["source_kinds"] == ["synthetic"]
    client = TestClient(create_app(settings))
    url = "/api/v1/reports?period=2024-04"
    assert (
        client.get(url + "&source_kind=synthetic").json()["items"][0]["report_id"]
        == report["report_id"]
    )
    assert client.get(url + "&source_kind=public").json()["items"] == []
    assert client.get("/api/v1/reports?period=2024-05").json()["items"] == []
    for period in ("0000-01", "9999-12", "2024-13", "202404"):
        assert client.get("/api/v1/reports?period=" + period).status_code == 422
        assert client.get("/api/v1/overview?period=" + period).status_code == 422
    assert client.get(url + "&source_kind=customer").status_code == 422
    catalog = Catalog(settings)
    with catalog.engine.begin() as conn:
        legacy = dict(report)
        legacy.pop("source_kinds")
        conn.execute(update(active_reports).values(payload=legacy))
    assert client.get(url + "&source_kind=synthetic").json()["items"][0]["source_kinds"] == [
        "synthetic"
    ]
    # Reads must not rewrite the historical database payload or immutable manifest.
    with catalog.engine.connect() as conn:
        assert "source_kinds" not in conn.execute(select(active_reports.c.payload)).scalar_one()
    other = Settings(
        root=settings.root, database_url=settings.database_url, org="other", s3_endpoint=None
    )
    assert TestClient(create_app(other)).get(url).json()["items"] == []
    # An unavailable legacy artifact must not be guessed as public or break other reports.
    with catalog.engine.begin() as conn:
        legacy["artifacts"] = dict(
            legacy["artifacts"], **{"manifest.json": str(settings.root / "unavailable.json")}
        )
        conn.execute(update(active_reports).values(payload=legacy))
    unknown = client.get(url).json()["items"][0]
    assert unknown["source_kinds"] is None and unknown["source_metadata_status"] == "unavailable"
    assert client.get(url + "&source_kind=synthetic").json()["items"] == []
    assert json.loads(
        (settings.root / "reports" / "demo" / report["report_id"] / "manifest.json").read_text(
            encoding="utf-8"
        )
    )["source_kinds"] == ["synthetic"]
