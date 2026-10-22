"""DuckDB external sort + bounded batches; retain all original columns as evidence."""

import json
import math
from datetime import UTC, datetime

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from solarops.contracts.brpvgen import flag, headers


def sql_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def rows(path, kind, plant, start, end):
    fields = headers(path, kind)
    conn = duckdb.connect()
    conn.execute("SET memory_limit='512MB'")
    conn.execute("SET threads=2")
    conn.execute("SET TimeZone='UTC'")
    order = (
        "TRY_CAST(datetime AS TIMESTAMPTZ), inverter_id"
        if kind == "inverter"
        else "TRY_CAST(datetime AS TIMESTAMPTZ)"
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


def normalize(raw, kind):
    value = raw.get("datetime") or ""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("TIMESTAMP_TIMEZONE_MISSING")
    dt = dt.astimezone(UTC)
    if dt.minute % 15 or dt.second or dt.microsecond:
        raise ValueError("TIMESTAMP_OFF_GRID")
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
    inv = int(raw["inverter_id"]) if kind == "inverter" else 0
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
