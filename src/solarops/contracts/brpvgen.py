import csv
import math
from pathlib import Path

from solarops.config import identifier

REQUIRED = {
    "inverter": {"datetime", "ps_id", "inverter_id", "total_active_power_w"},
    "station": {"datetime", "ps_id", "poa_irradiance_wm2"},
}


def read_metadata(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not {"id", "nominal_power_mw"} <= set(fields):
            raise ValueError("Metadata contract mismatch")
        result = {}
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("Metadata contract row width mismatch")
            plant = identifier(row["id"])
            capacity = float(row["nominal_power_mw"]) * 1000
            if not math.isfinite(capacity) or capacity <= 0 or plant in result:
                raise ValueError("Invalid/duplicate metadata plant")
            result[plant] = dict(row, plant_id=plant, nominal_power_kw=capacity)
        return result


def headers(path, kind):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        fields = next(csv.reader(f))
    if len(fields) != len(set(fields)) or not REQUIRED[kind] <= set(fields):
        raise ValueError(f"{kind} contract mismatch: {fields}")
    return fields


def flag(value):
    if value is None or value == "":
        return None
    if str(value).lower() in ("true", "1"):
        return True
    if str(value).lower() in ("false", "0"):
        return False
    raise ValueError("Invalid interpolation flag")
