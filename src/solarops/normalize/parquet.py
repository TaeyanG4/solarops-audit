"""DuckDB external sort + bounded batches; retain all original columns as evidence."""

import json
import math
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from solarops.contracts.brpvgen import flag, headers


def sql_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def inverter_id(value):
    """One canonical, nonnegative int64 ID in bounds, keys and Parquet."""
    if not isinstance(value, str) or not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("NONCANONICAL_INVERTER_ID")
    result = int(value)
    if result > 2**63 - 1:
        raise ValueError("INVERTER_ID_OUT_OF_RANGE")
    return result


def configure_duckdb(conn):
    conn.execute("SET memory_limit='512MB'")
    conn.execute("SET threads=2")
    conn.execute("SET TimeZone='UTC'")
    if directory := os.getenv("SOLAROPS_DUCKDB_TEMP_DIR"):
        # Separate connections must never share spill files. Pod /tmp is writable.
        path = Path(directory) / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        conn.execute("SET temp_directory=" + sql_quote(path))


def rows(path, kind, plant, start, end):
    fields = headers(path, kind)
    conn = duckdb.connect()
    configure_duckdb(conn)
    order = (
        "TRY_CAST(datetime AS TIMESTAMPTZ) NULLS FIRST, inverter_id"
        if kind == "inverter"
        else "TRY_CAST(datetime AS TIMESTAMPTZ) NULLS FIRST"
    )
    query = f"""SELECT * FROM read_csv({sql_quote(path)}, all_varchar=true)
      WHERE ps_id={sql_quote(plant)} AND
      (TRY_CAST(datetime AS TIMESTAMPTZ) IS NULL OR
       (TRY_CAST(datetime AS TIMESTAMPTZ)>={sql_quote(start)}::TIMESTAMPTZ
        AND TRY_CAST(datetime AS TIMESTAMPTZ)<{sql_quote(end)}::TIMESTAMPTZ))
      ORDER BY {order}"""
    try:
        cursor = conn.execute(query)
        while batch := cursor.fetchmany(2048):
            for values in batch:
                yield dict(zip(fields, values, strict=True))
    finally:
        conn.close()


def timestamp_utc(value):
    """The same timestamp contract for source bounds and normalized observations."""
    try:
        dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("TIMESTAMP_INVALID") from None
    if dt.tzinfo is None:
        raise ValueError("TIMESTAMP_TIMEZONE_MISSING")
    # Python also accepts compact/week dates and arbitrary separators that SQL
    # cannot sort. Admit only the shared, lossless wire format before grouping.
    if not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])",
        value,
    ):
        raise ValueError("TIMESTAMP_FORMAT")
    try:
        dt = dt.astimezone(UTC)
    except (ValueError, OverflowError):
        raise ValueError("TIMESTAMP_INVALID") from None
    if dt.minute % 15 or dt.second or dt.microsecond:
        raise ValueError("TIMESTAMP_OFF_GRID")
    return dt


def normalize(raw, kind):
    dt = timestamp_utc(raw.get("datetime"))
    field = "total_active_power_w" if kind == "inverter" else "poa_irradiance_wm2"
    numeric = raw.get(field)
    numeric = float(numeric) if numeric not in (None, "") else None
    valid = numeric is not None and math.isfinite(numeric) and numeric >= 0
    if numeric is not None and not math.isfinite(numeric):
        numeric = None
    interpolation = flag(raw.get("interpolated_keys_" + field))
    count = raw.get("document_count_" + field)
    count = int(count) if count not in (None, "") else None
    if count is not None and count < 0:
        raise ValueError("NEGATIVE_DOCUMENT_COUNT")
    inv = inverter_id(raw.get("inverter_id")) if kind == "inverter" else 0
    return {
        "ts_utc": dt.isoformat(),
        "plant_id": raw["ps_id"],
        "inverter_id": inv,
        "value": numeric,
        "valid": valid,
        "interpolated": interpolation,
        "document_count": count,
        "raw_json": json.dumps(raw, sort_keys=True, separators=(",", ":")),
    }


SCHEMA = pa.schema(
    [
        ("ts_utc", pa.string()),
        ("plant_id", pa.string()),
        ("inverter_id", pa.int64()),
        ("value", pa.float64()),
        ("valid", pa.bool_()),
        ("interpolated", pa.bool_()),
        ("document_count", pa.int64()),
        ("raw_json", pa.string()),
        ("source_object_id", pa.string()),
        ("ingest_run_id", pa.string()),
    ]
)


def write_parquet(path, data, source_id, run_id):
    path.parent.mkdir(parents=True, exist_ok=True)
    enriched = [dict(row, source_object_id=source_id, ingest_run_id=run_id) for row in data]
    pq.write_table(pa.Table.from_pylist(enriched, schema=SCHEMA), path, compression="zstd")
