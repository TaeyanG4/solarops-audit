import zipfile
from datetime import UTC, datetime

import pytest

from solarops.acquisition.brpvgen import safe_extract
from solarops.analytics.metrics import analyze, day_window
from solarops.config import identifier
from solarops.contracts.brpvgen import flag, read_metadata
from solarops.normalize.parquet import normalize
from solarops.pipeline import deduplicate, source_bounds


def ons_csv(path, values):
    """Small offline source-native fixture; (day, hour, value, mode, id) tuples."""
    import csv

    from solarops.acquisition.ons import FIELDS

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        for day, hour, value, mode, entity in values:
            writer.writerow(
                dict(
                    zip(
                        FIELDS,
                        [
                            f"2026-10-{day:02d} {hour:02d}:00:00",
                            "NE",
                            "NORDESTE",
                            "BA",
                            "BAHIA",
                            mode,
                            "FOTOVOLTAICA",
                            "Fotovoltaica",
                            entity or "GROUP",
                            entity,
                            "-",
                            value,
                        ],
                        strict=True,
                    )
                )
            )
    return path


def test_ons_native_time_unit_basis_invalids_and_duplicate_conflict(tmp_path):
    import json

    from solarops.acquisition.ons import CONTRACT, parse

    values = [
        (1, 0, "0", "TIPO II-B", "A"),
        (1, 1, "nan", "TIPO II-B", "A"),
        (1, 0, "2", "Pequenas Usinas (Tipo III)", ""),
        (1, 0, "3", "Pequenas Usinas (MMGD)", ""),
    ]
    path = ons_csv(tmp_path / "source.csv", values + [values[0]])
    days, count = parse(path, "2026-10")
    payload = json.loads(days["2026-10-01"][1])
    assert count == 5 and payload["quality"]["rows"] == 4
    assert payload["quality"]["duplicate_rows"] == 1
    assert payload["quality"]["invalid_values"] == 1
    assert payload["quality"]["missing_hour_labels_present_entities"] == 68
    assert payload["quality"]["generation_basis_counts"] == {
        "verified": 2,
        "forecast": 1,
        "unspecified": 1,
    }
    assert all(r["ts_utc"] is None for r in payload["items"])
    assert CONTRACT["unit"] == "MWmed" and not CONTRACT["energy_conversion"]
    ons_csv(path, values + [(1, 0, "9", "TIPO II-B", "A")])
    with pytest.raises(ValueError, match="ONS_DUPLICATE_CONFLICT"):
        parse(path, "2026-10")
    with pytest.raises(ValueError, match="ONS_TIMESTAMP"):
        parse(path, "2026-09")
    path.write_text(
        path.read_text(encoding="utf-8").replace("00:00:00", "00:30:00"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="ONS_TIMESTAMP"):
        parse(path, "2026-10")


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


def test_inverter_identity_is_consistent_in_bounds_and_rows(tmp_path):
    for value in ("01", "+1", " 1", "1.0", "-1", "9223372036854775808"):
        with pytest.raises(ValueError, match="INVERTER_ID"):
            record(inv=value)
        path = tmp_path / "aliases.csv"
        path.write_text(
            "datetime,ps_id,inverter_id\n"
            f"2024-04-01T00:00:00Z,DEMO_01,{value}\n"
            "2024-04-01T00:15:00Z,DEMO_01,1\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="INVERTER_ID"):
            source_bounds(path, "DEMO_01", {"DEMO_01"})
    assert record(inv="1")["inverter_id"] == 1


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


def test_interrupted_extraction_is_not_visible_and_can_retry(tmp_path, monkeypatch):
    from solarops.acquisition import brpvgen

    archive, destination = tmp_path / "input.zip", tmp_path / "extracted"
    content = b"datetime,value\n2024-04-01,100\n"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("sample.csv", content)
    original = brpvgen.shutil.copyfileobj

    def interrupted(source, output, *args):
        output.write(source.read(4))
        raise OSError("interrupted")

    monkeypatch.setattr(brpvgen.shutil, "copyfileobj", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        safe_extract(archive, destination)
    assert not (destination / "sample.csv").exists()
    partial = list(destination.glob("*.partial-*"))[0]
    assert partial.read_bytes() == content[:4]
    monkeypatch.setattr(brpvgen.shutil, "copyfileobj", original)
    safe_extract(archive, destination)
    safe_extract(archive, destination)
    assert (destination / "sample.csv").read_bytes() == content
    assert partial.read_bytes() == content[:4]
    assert archive.exists()
