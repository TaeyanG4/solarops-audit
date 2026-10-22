import zipfile
from datetime import UTC, datetime

import pytest

from solarops.acquisition.brpvgen import safe_extract
from solarops.analytics.metrics import analyze, day_window
from solarops.config import identifier
from solarops.contracts.brpvgen import flag, read_metadata
from solarops.normalize.parquet import normalize
from solarops.pipeline import deduplicate


def record(ts="2024-04-01T00:00:00Z", power="1000", inv=1, interpolated="false"):
    return normalize(
        {
            "datetime": ts,
            "ps_id": "DEMO_01",
            "inverter_id": str(inv),
            "total_active_power_w": power,
            "interpolated_keys_total_active_power_w": interpolated,
            "document_count_total_active_power_w": "3",
        },
        "inverter",
    )


@pytest.mark.parametrize("bad", ["../org", "a/b", "", "x:y", "a\\b"])
def test_identifier_rejects_paths(bad):
    with pytest.raises(ValueError):
        identifier(bad)


@pytest.mark.parametrize("value,expected", [("true", True), ("0", False), (None, None), ("", None)])
def test_flags(value, expected):
    assert flag(value) is expected


@pytest.mark.parametrize("ts", ["garbage", "2024-04-01T00:00:00", "2024-04-01T00:01:00Z"])
def test_bad_timestamps(ts):
    with pytest.raises(ValueError):
        record(ts)


def test_offsets_are_utc():
    assert record("2024-04-01T09:00:00+09:00")["ts_utc"] == "2024-04-01T00:00:00+00:00"


def test_golden_energy_duplicates_and_missing():
    data = [
        record(power="1000"),
        record(power="2000", inv=2),
        record("2024-04-01T00:15:00Z", "2000"),
        record("2024-04-01T00:15:00Z", "3000", 2),
    ]
    clean, count = deduplicate(data + [data[0]])
    a, b = datetime(2024, 4, 1, tzinfo=UTC), datetime(2024, 4, 1, 0, 30, tzinfo=UTC)
    metric, issues, _, _ = analyze(clean, [], 20, {1: (a, b), 2: (a, b)}, "2024-04-01", "UTC")
    assert metric["estimated_energy_kwh"] == 2.0
    assert metric["missing_slots"] == 2
    assert count == 1
    assert issues[0]["rule_id"] == "DQ-MISSING"


@pytest.mark.parametrize("power", ["-2", "nan", "inf", ""])
def test_invalid_power_not_estimated(power):
    r = record(power=power)
    assert not r["valid"]


def test_conflict_is_not_last_write_wins():
    with pytest.raises(ValueError, match="DUPLICATE_CONFLICT"):
        deduplicate([record(power="1000"), record(power="2000")])


@pytest.mark.parametrize(
    "interpolated,poa,minutes,expected",
    [
        ("false", "500", (0, 15, 30), 1),
        ("true", "500", (0, 15, 30), 0),
        ("false", "0", (0, 15, 30), 0),
        ("", "500", (0, 15, 30), 0),
        ("false", "500", (0, 15), 0),
        ("false", "500", (0, 15, 45), 0),
    ],
)
def test_review_requires_reliable_daylight(interpolated, poa, minutes, expected):
    inv, sta = [], []
    for minute in minutes:
        ts = f"2024-04-01T12:{minute:02d}:00Z"
        inv.append(record(ts, "10", interpolated=interpolated))
        sta.append(
            normalize(
                {
                    "datetime": ts,
                    "ps_id": "DEMO_01",
                    "poa_irradiance_wm2": poa,
                    "interpolated_keys_poa_irradiance_wm2": "false",
                    "document_count_poa_irradiance_wm2": "3",
                },
                "station",
            )
        )
    bounds = {
        1: (datetime.fromisoformat(inv[0]["ts_utc"]), datetime.fromisoformat(inv[-1]["ts_utc"]))
    }
    _, _, events, _ = analyze(inv, sta, 20, bounds, "2024-04-01", "UTC")
    assert len(events) == expected


def test_dst_denominator():
    a, b = day_window("2024-03-10", "America/New_York")
    assert (b - a).total_seconds() / 3600 == 23


def test_metadata_string_id_and_mw_conversion(sample):
    assert read_metadata(sample["metadata"])["DEMO_01"]["nominal_power_kw"] == 20


@pytest.mark.parametrize(
    "name", ["../evil.csv", "/evil.csv", "C:/evil.csv", "..\\evil.csv", "script.exe"]
)
def test_zip_paths_and_extensions(tmp_path, name):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(name, "test")
    with pytest.raises(ValueError):
        safe_extract(archive, tmp_path / "out")


def test_zip_expansion_cap(tmp_path):
    archive = tmp_path / "big.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("a.csv", "x" * 100)
    with pytest.raises(ValueError):
        safe_extract(archive, tmp_path / "out", limit=10)
