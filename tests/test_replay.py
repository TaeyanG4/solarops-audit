import json
from pathlib import Path

import pytest

from solarops.cli import main
from solarops.pipeline import ingest
from solarops.replay import replay
from solarops.storage.postgres import Catalog


@pytest.fixture
def public_layout(settings, sample, tmp_path):
    # Tiny synthetic CSVs with public-style IDs; no network or real dataset required.
    settings.source_root = tmp_path / "public-source"
    paths = {
        "metadata": settings.source_root / "BR-PVGen_metadata.csv",
        "inverter": settings.source_root / "inverter/BR-PVGen_inverter/PS_001.csv",
        "station": settings.source_root / "station/BR-PVGen_meteorological/PS_001.csv",
    }
    for kind, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sample[kind].read_text().replace("DEMO_01", "PS_001"), encoding="utf-8")
    return paths


def public_replay(settings, **kwargs):
    args = dict(
        source_kind="public",
        plant="PS_001",
        start="2024-04-03",
        end="2024-04-04",
        source_version="public-test-v1",
    )
    args.update(kwargs)
    return replay(settings, **args)


def test_dry_run_checks_inputs_without_publishing(settings, public_layout):
    before = {p: p.read_bytes() for p in public_layout.values()}
    plan = public_replay(settings)
    assert plan["dry_run"] is True and plan["days"] == 1
    assert plan["plant_id"] == "PS_001" and plan["report_timezone"] == "UTC"
    assert not settings.root.exists()
    assert not (settings.root.parent / "catalog.db").exists()
    assert before == {p: p.read_bytes() for p in public_layout.values()}


def test_public_replay_matches_ingest_and_preserves_other_days(settings, public_layout):
    ingest(
        settings,
        public_layout["metadata"],
        public_layout["inverter"],
        public_layout["station"],
        "PS_001",
        "2024-04-01",
        "2024-04-08",
        "public-test-v1",
        "public",
    )
    before = {r["partition_id"]: r for r in Catalog(settings).snapshot("demo")}
    result = public_replay(settings, dry_run=False)
    after = {r["partition_id"]: r for r in Catalog(settings).snapshot("demo")}
    assert result["partitions"] == 1 and result["rows"] == 192
    assert [day for day in before if before[day]["run_id"] != after[day]["run_id"]] == [
        "2024-04-03"
    ]
    assert all(
        before[d]["payload"]["logical_content_hash"] == after[d]["payload"]["logical_content_hash"]
        for d in before
    )
    assert all(
        s["source_kind"] == "public" for s in after["2024-04-03"]["payload"]["source_objects"]
    )


@pytest.mark.parametrize(
    "start,end",
    [("2024-04-01", "2024-05-03"), ("2024-04-02", "2024-04-02"), ("2024-04-02", "2024-04-01")],
)
def test_replay_rejects_unbounded_window(settings, start, end):
    with pytest.raises(ValueError, match="1–31 days"):
        public_replay(settings, start=start, end=end)


@pytest.mark.parametrize("plant", ["../PS_001", "--help", "DEMO_01", "PS_001/secret"])
def test_public_replay_rejects_paths_and_wrong_plant(settings, plant):
    with pytest.raises(ValueError):
        public_replay(settings, plant=plant)


def test_public_replay_requires_sources_and_overlapping_window(settings, public_layout):
    with pytest.raises(ValueError, match="NO_SOURCE_DATA_IN_WINDOW"):
        public_replay(settings, start="2025-01-01", end="2025-01-02")
    settings.source_root = settings.source_root / "missing"
    with pytest.raises(ValueError, match="MISSING_PUBLIC_SOURCE"):
        public_replay(settings)


def test_public_replay_rejects_other_org(settings, public_layout):
    settings.org = "other"
    with pytest.raises(ValueError, match="demo org"):
        public_replay(settings)


def test_source_symlink_cannot_escape_root(settings, public_layout, tmp_path):
    outside = tmp_path / "outside.csv"
    outside.write_bytes(public_layout["metadata"].read_bytes())
    # Use a new root so the original input is preserved.
    settings.source_root = tmp_path / "linked-root"
    settings.source_root.mkdir()
    try:
        (settings.source_root / "BR-PVGen_metadata.csv").symlink_to(outside)
    except OSError:
        pytest.skip("Host does not permit test symlinks")
    with pytest.raises(ValueError, match="SOURCE_PATH_OUTSIDE_ROOT"):
        public_replay(settings)


def test_synthetic_replay_uses_settings_and_keeps_report(settings):
    result = replay(settings, "synthetic", "DEMO_01", "2024-04-03", "2024-04-04", "v1", False)
    assert result["partitions"] == 1 and result["report"]["scope"] == "DEMO_01"
    assert len(Catalog(settings).snapshot("demo", source_kind="synthetic")) == 1
    assert not Catalog(settings).snapshot("demo", source_kind="public")
    with pytest.raises(ValueError, match="fixture covers"):
        replay(settings, "synthetic", "DEMO_01", "2024-05-01", "2024-05-02", "v1")


def test_cli_plan_and_scoped_month_analysis(settings, public_layout, monkeypatch, capsys):
    monkeypatch.setenv("SOLAROPS_DATA_DIR", str(settings.root))
    monkeypatch.setenv("SOLAROPS_DATABASE_URL", settings.database_url)
    monkeypatch.setenv("SOLAROPS_SOURCE_DIR", str(settings.source_root))
    assert (
        main(
            [
                "replay",
                "--source-kind",
                "public",
                "--plant",
                "PS_001",
                "--from",
                "2024-04-03",
                "--to",
                "2024-04-04",
                "--source-version",
                "public-test-v1",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["dry_run"] is True
    public_replay(settings, dry_run=False)
    replay(settings, "synthetic", "DEMO_01", "2024-04-03", "2024-04-04", "v1", False)
    args = ["analyze", "--period", "2024-04", "--plant", "PS_001", "--source-kind", "public"]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["partitions"] == 1 and result["metrics"][0]["plant_id"] == "PS_001"
    assert (
        main(["report", "--period", "2024-04", "--plant", "PS_001", "--source-kind", "public"]) == 0
    )
    report = json.loads(capsys.readouterr().out)
    manifest = json.loads((Path(report["local_directory"]) / "manifest.json").read_text())
    assert manifest["public"] is True and manifest["synthetic"] is False
    assert manifest["plant_count"] == 1 and manifest["days"] == 1
    assert main([*args[:-1], "synthetic"]) == 1
    assert "NO_ACTIVE_PARTITIONS" in capsys.readouterr().err
    assert main([*args, "--from", "2024-04-01"]) == 1
    assert "Use --period or" in capsys.readouterr().err
