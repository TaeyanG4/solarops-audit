import csv
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(directory: Path):
    """Small deterministic synthetic demo, with labeled test injections."""
    paths = {k: directory / f"{k}.csv" for k in ("metadata", "inverter", "station")}
    if any(p.exists() for p in paths.values()):
        if not all(p.exists() for p in paths.values()):
            raise ValueError("Incomplete fixture directory; choose a new directory")
        return paths
    write_csv(
        paths["metadata"],
        ["id", "nominal_power_mw", "brazil_federative_unit", "structure_type"],
        [
            {
                "id": "DEMO_01",
                "nominal_power_mw": 0.02,
                "brazil_federative_unit": "SYNTHETIC",
                "structure_type": "FIXED",
            }
        ],
    )
    inv, sta = [], []
    for slot in range(7 * 96):
        dt = datetime(2024, 4, 1, tzinfo=UTC) + timedelta(minutes=slot * 15)
        ts = dt.isoformat().replace("+00:00", "Z")
        sunlight = (
            max(0, math.sin((dt.hour + dt.minute / 60 - 6) / 12 * math.pi))
            if 6 <= dt.hour < 18
            else 0
        )
        poa = round(sunlight * 900, 3)
        sta.append(
            {
                "datetime": ts,
                "ps_id": "DEMO_01",
                "poa_irradiance_wm2": poa,
                "interpolated_keys_poa_irradiance_wm2": "true" if slot == 244 else "false",
                "document_count_poa_irradiance_wm2": 3,
            }
        )
        for inverter in (1, 2):
            if slot in (140, 141) and inverter == 2:
                continue
            power = round(sunlight * 8000, 3)
            if 428 <= slot <= 432:
                power = 300
            inv.append(
                {
                    "datetime": ts,
                    "ps_id": "DEMO_01",
                    "inverter_id": inverter,
                    "total_active_power_w": power,
                    "interpolated_keys_total_active_power_w": "true" if slot == 245 else "false",
                    "document_count_total_active_power_w": 3,
                }
            )
    inv.append(dict(inv[10]))
    write_csv(paths["inverter"], list(inv[0]), inv)
    write_csv(paths["station"], list(sta[0]), sta)
    return paths
