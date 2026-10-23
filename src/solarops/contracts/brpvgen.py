import csv
import math
from pathlib import Path

from solarops.config import identifier

REQUIRED = {
    "inverter": {"datetime", "ps_id", "inverter_id", "total_active_power_w"},
    "station": {"datetime", "ps_id", "poa_irradiance_wm2"},
}

ERROR_CODES = frozenset(
    {
        "UNKNOWN_PLANT_IN_SOURCE",
        "UNKNOWN_PLANT",
        "DUPLICATE_CONFLICT",
        "SOURCE_VERSION_CONFLICT",
        "HISTORICAL_RESTORE_REQUIRES_FLAG",
        "SOURCE_RANGE_SHRINK",
        "RAW_OBJECT_CHECKSUM_MISMATCH",
        "PUBLICATION_CONFLICT",
        "METRIC_CONTRACT_MISMATCH",
        "PLANT_METADATA_CONFLICT",
        "INJECTED_BEFORE_COMMIT",
        "INJECTED_DURING_COMMIT",
        "NONCANONICAL_INVERTER_ID",
        "INVERTER_ID_OUT_OF_RANGE",
        "TIMESTAMP_INVALID",
        "TIMESTAMP_TIMEZONE_MISSING",
        "TIMESTAMP_OFF_GRID",
        "TIMESTAMP_FORMAT",
        "NEGATIVE_DOCUMENT_COUNT",
        "INVERTER_VALUE_NOT_NUMERIC",
        "STATION_VALUE_NOT_NUMERIC",
        "INVERTER_INTERPOLATION_INVALID",
        "STATION_INTERPOLATION_INVALID",
        "INVERTER_DOCUMENT_COUNT_INVALID",
        "STATION_DOCUMENT_COUNT_INVALID",
        "SOURCE_PATH_OUTSIDE_ROOT",
        "MISSING_PUBLIC_SOURCE",
        "NO_SOURCE_DATA_IN_WINDOW",
        "NO_ACTIVE_PARTITIONS",
    }
)


def failure_code(exc):
    """Persist/print a classification, never arbitrary source or connection text."""
    from botocore.exceptions import BotoCoreError, ClientError
    from duckdb import Error as DuckDBError
    from sqlalchemy.exc import SQLAlchemyError

    if isinstance(exc, (ValueError, RuntimeError)):
        code = str(exc).split(":", 1)[0]
        if code in ERROR_CODES:
            return code
    if isinstance(exc, (ValueError, DuckDBError)):
        return "BR_INPUT_INVALID"
    if isinstance(exc, SQLAlchemyError):
        return "BR_CATALOG_ERROR"
    if isinstance(exc, (BotoCoreError, ClientError)):
        return "BR_OBJECT_STORE_ERROR"
    if isinstance(exc, OSError):
        return "BR_IO_ERROR"
    return "BR_UNEXPECTED_ERROR"


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
