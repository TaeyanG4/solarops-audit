import csv
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from solarops.analytics.metrics import analyze
from solarops.api.readmodels import fleet_overview
from solarops.config import CALCULATION_VERSION
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog
from tests.test_contracts import record
from tests.test_pipeline import run


@pytest.mark.parametrize(
    "values,expected_power,energy",
    [(("", "-1"), None, 0), (("0", "0"), 0, 0), (("1000", ""), 1, 0.25)],
)
def test_series_distinguishes_invalid_zero_and_partial(values, expected_power, energy):
    rows = [record(power=value, inv=i + 1) for i, value in enumerate(values)]
    ts = datetime.fromisoformat(rows[0]["ts_utc"])
    bounds = {r["inverter_id"]: (ts, ts) for r in rows}
    metric, _, candidates, series = analyze(rows, [], 20, bounds, "2024-04-01", "UTC")
    assert series[0]["power_kw"] == expected_power
    assert metric["estimated_energy_kwh"] == energy
    assert series[0]["assessment"] == "INSUFFICIENT_DATA" and not candidates


def sparse_source(sample, timestamps):
    with sample["inverter"].open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "datetime",
                "ps_id",
                "inverter_id",
                "total_active_power_w",
                "interpolated_keys_total_active_power_w",
                "document_count_total_active_power_w",
            ]
        )
        for ts in timestamps:
            writer.writerow([ts, "DEMO_01", 1, 1000, "false", 3])
    with sample["station"].open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["datetime", "ps_id", "poa_irradiance_wm2"])


@pytest.mark.parametrize(
    "zone,timestamps,expected",
    [
        ("Asia/Seoul", ["2024-04-01T23:30:00Z", "2024-04-02T00:30:00Z"], "2024-04-02"),
        ("America/Sao_Paulo", ["2024-04-02T00:00:00Z", "2024-04-02T01:00:00Z"], "2024-04-01"),
    ],
)
def test_no_partition_outside_local_source_bounds(settings, sample, zone, timestamps, expected):
    sparse_source(sample, timestamps)
    local = replace(settings, timezone=zone)
    result = run(local, sample, end="2024-04-04")
    assert [r["day"] for r in result["results"]] == [expected]
    metric = Catalog(local).snapshot("demo")[0]["metric"]
    assert metric["expected_slots"] == 5
    assert metric["observed_slots"] == 2 and metric["missing_slots"] == 3


@pytest.mark.parametrize(
    "day,timestamps,slots",
    [
        ("2024-03-10", ["2024-03-09T12:00:00Z", "2024-03-11T12:00:00Z"], 92),
        ("2024-11-03", ["2024-11-02T12:00:00Z", "2024-11-04T12:00:00Z"], 100),
    ],
)
def test_entire_missing_dst_day_is_published(settings, sample, day, timestamps, slots):
    sparse_source(sample, timestamps)
    local = replace(settings, timezone="America/New_York")
    end = day[:-2] + f"{int(day[-2:]) + 1:02d}"
    result = run(local, sample, start=day, end=end)
    assert result["partitions"] == 1
    row = Catalog(local).snapshot("demo")[0]
    assert row["metric"]["expected_slots"] == row["metric"]["missing_slots"] == slots
    series = json.loads((local.root / row["payload"]["object_prefix"] / "series.json").read_text())
    assert len(series) == slots and all(r["power_kw"] is None for r in series)
    assert row["metric"]["source_interpolation_ratio"] is None
    assert fleet_overview(Catalog(local), day[:7])["summary"]["source_interpolation_ratio"] is None
    report = build_report(local, day[:7], "DEMO_01", "synthetic")
    directory = Path(report["local_directory"])
    original = (directory / "manifest.json").read_bytes()
    assert json.loads(original)["interpolation"] is None
    assert "<dt>원본 보간 표시</dt><dd>알 수 없음" in (directory / "report.html").read_text(
        encoding="utf-8"
    )
    # A real observed non-interpolated value remains 0%, and old reports stay immutable.
    sparse_source(sample, [f"{day}T12:00:00Z"])
    run(local, sample, version="filled", start=day, end=end)
    newer = build_report(local, day[:7], "DEMO_01", "synthetic")
    assert (
        json.loads((Path(newer["local_directory"]) / "manifest.json").read_text(encoding="utf-8"))[
            "interpolation"
        ]
        == 0
    )
    assert (directory / "manifest.json").read_bytes() == original
    # Observed rows with unknown flags must not look like explicit False.
    for label, flags, ratio, unknown in (
        ("unknown", ["", "", ""], None, 3),
        ("mixed", ["true", "false", ""], 1 / 3, 1),
        ("false", ["false", "false", "false"], 0, 0),
    ):
        sparse_source(sample, [f"{day}T12:{minute:02d}:00Z" for minute in (0, 15, 30)])
        with sample["inverter"].open(encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
        for raw_record, value in zip(records, flags, strict=True):
            raw_record["interpolated_keys_total_active_power_w"] = value
        with sample["inverter"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        run(local, sample, version=label, start=day, end=end)
        result = build_report(local, day[:7], "DEMO_01", "synthetic")
        target = Path(result["local_directory"])
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["interpolation"] == ratio
        assert manifest["interpolation_unknown_slots"] == unknown
        html = (target / "report.html").read_text(encoding="utf-8")
        if label == "unknown":
            assert "<dt>원본 보간 표시</dt><dd>알 수 없음" in html
        elif label == "mixed":
            assert "33.33% 확인 · 불명 1슬롯" in html
        else:
            assert "<dt>원본 보간 표시</dt><dd>0.00%" in html
        assert (directory / "manifest.json").read_bytes() == original


def test_v2_hash_includes_series_and_retains_replay_determinism(settings, sample, monkeypatch):
    import solarops.pipeline as pipeline

    assert CALCULATION_VERSION == "energy-interval-v2"
    original = pipeline.analyze
    first = run(settings, sample, end="2024-04-02")["results"][0]["logical_hash"]
    assert run(settings, sample, end="2024-04-02")["results"][0]["logical_hash"] == first

    def changed_series(*args, **kwargs):
        metric, issues, candidates, series = original(*args, **kwargs)
        series[0]["power_kw"] = 12345
        return metric, issues, candidates, series

    monkeypatch.setattr(pipeline, "analyze", changed_series)
    changed = run(settings, sample, end="2024-04-02")["results"][0]["logical_hash"]
    assert changed != first
