import hashlib
import itertools
import json
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import duckdb
from sqlalchemy import select, text

from solarops.acquisition.brpvgen import DOI, checksum
from solarops.analytics.metrics import analyze
from solarops.config import CALCULATION_VERSION, identifier
from solarops.contracts.brpvgen import read_metadata
from solarops.normalize.parquet import normalize, rows, sql_quote, write_parquet
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import (
    Catalog,
    active,
    events,
    issues,
    metrics,
    now,
    plants,
    put,
    runs,
    sources,
    versions,
)


def canonical_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def source_bounds(path, plant, metadata_ids):
    with duckdb.connect() as conn:
        conn.execute("SET memory_limit='512MB'")
        conn.execute("SET threads=2")
        q = f"read_csv({sql_quote(path)}, all_varchar=true)"
        unknown = {r[0] for r in conn.execute(f"SELECT DISTINCT ps_id FROM {q}").fetchall()} - set(
            metadata_ids
        )
        if unknown:
            raise ValueError("UNKNOWN_PLANT_IN_SOURCE")
        data = conn.execute(
            f"SELECT inverter_id, min(try_cast(datetime AS TIMESTAMPTZ)), max(try_cast(datetime AS TIMESTAMPTZ)) FROM {q} WHERE ps_id=? GROUP BY inverter_id",
            [plant],
        ).fetchall()
    return {
        int(inv): (left.astimezone(UTC), right.astimezone(UTC))
        for inv, left, right in data
        if left and right
    }


def normalized_days(path, kind, plant, start, end, timezone):
    zone = ZoneInfo(timezone)
    iterator = (normalize(r, kind) for r in rows(path, kind, plant, start, end))
    for day, group in itertools.groupby(
        iterator, lambda r: datetime.fromisoformat(r["ts_utc"]).astimezone(zone).date().isoformat()
    ):
        yield day, list(group)


def deduplicate(data):
    unique, duplicates = {}, 0
    for row in data:
        key = (row["ts_utc"], row["inverter_id"])
        if key in unique:
            if row != unique[key]:
                raise ValueError("DUPLICATE_CONFLICT")
            duplicates += 1
        else:
            unique[key] = row
    return [unique[k] for k in sorted(unique)], duplicates


def ingest(
    settings,
    metadata_path,
    inverter_path,
    station_path,
    plant,
    start,
    end,
    source_version,
    source_kind="synthetic",
    fail_at=None,
    poa_threshold=400,
    power_ratio=0.10,
):
    identifier(plant)
    identifier(source_version)
    if source_kind not in ("public", "synthetic"):
        raise ValueError(
            "Only public/synthetic inputs are enabled; customer approval workflow is not enabled"
        )
    if source_kind == "public" and settings.org != "demo":
        raise ValueError("Public BR-PVGen belongs to demo org")
    left, right = date.fromisoformat(start), date.fromisoformat(end)
    if left >= right or (right - left).days > 500:
        raise ValueError("Use a nonempty window of at most 500 days; --to is exclusive")
    zone = ZoneInfo(settings.timezone)
    begin_utc = datetime.combine(left, datetime.min.time(), zone).astimezone(UTC).isoformat()
    end_utc = datetime.combine(right, datetime.min.time(), zone).astimezone(UTC).isoformat()
    catalog, objects = Catalog(settings), ObjectStore(settings)
    meta = read_metadata(metadata_path)
    if plant not in meta:
        raise ValueError("UNKNOWN_PLANT")
    source_info = []
    for kind, path in (
        ("metadata", metadata_path),
        ("inverter", inverter_path),
        ("station", station_path),
    ):
        digest = checksum(path)
        sid = str(uuid.uuid5(uuid.NAMESPACE_URL, settings.org + ":" + digest))
        uri = objects.raw(path, settings.org, digest)
        info = {
            "source_object_id": sid,
            "sha256": digest,
            "original_filename": path.name,
            "origin_uri": DOI if source_kind == "public" else "synthetic-fixture",
            "raw_uri": uri,
            "source_version": source_version,
            "dataset_kind": kind,
            "license": "CC BY 4.0" if source_kind == "public" else "synthetic test data",
            "source_kind": source_kind,
            "source_preprocessed": True,
            "created_at": now(),
        }
        with catalog.engine.begin() as conn:
            # Source IDs are content-addressed within each organization.
            existing = conn.execute(
                select(sources).where(sources.c.source_object_id == sid)
            ).first()
            if not existing:
                put(
                    conn,
                    sources,
                    {"source_object_id": sid},
                    info,
                    org_id=settings.org,
                    sha256=digest,
                )
        source_info.append(info)
    fingerprint = canonical_hash([s["sha256"] for s in source_info])
    version_key = {"org_id": settings.org, "plant_id": plant, "source_version": source_version}
    with catalog.engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": json.dumps(version_key, sort_keys=True)},
            )
        existing = conn.execute(select(versions).filter_by(**version_key)).mappings().first()
        if existing and existing["payload"]["fingerprint"] != fingerprint:
            raise ValueError("SOURCE_VERSION_CONFLICT: use a new explicit version")
        put(
            conn, versions, version_key, {"fingerprint": fingerprint, "source_objects": source_info}
        )
        put(conn, plants, {"org_id": settings.org, "plant_id": plant}, meta[plant])
    batch_id = str(uuid.uuid4())
    with catalog.engine.begin() as conn:
        put(
            conn,
            runs,
            {"run_id": batch_id},
            {"kind": "ingest", "plant_id": plant, "from": start, "to": end, "started_at": now()},
            org_id=settings.org,
            status="running",
        )
    outcomes = []
    try:
        bounds = source_bounds(inverter_path, plant, meta)
        inv_iter = iter(
            normalized_days(inverter_path, "inverter", plant, begin_utc, end_utc, settings.timezone)
        )
        station_iter = iter(
            normalized_days(station_path, "station", plant, begin_utc, end_utc, settings.timezone)
        )
        inv_day, sta_day = next(inv_iter, None), next(station_iter, None)
        for offset in range((right - left).days):
            day = (left + timedelta(days=offset)).isoformat()
            inv_rows = inv_day[1] if inv_day and inv_day[0] == day else []
            sta_rows = sta_day[1] if sta_day and sta_day[0] == day else []
            # Outside observed source bounds, do not invent expected coverage.
            if inv_rows or any(
                a.date().isoformat() <= day <= b.date().isoformat() for a, b in bounds.values()
            ):
                outcomes.append(
                    publish_day(
                        catalog,
                        objects,
                        settings,
                        plant,
                        day,
                        source_version,
                        source_info,
                        meta[plant],
                        bounds,
                        inv_rows,
                        sta_rows,
                        fail_at,
                        poa_threshold,
                        power_ratio,
                    )
                )
            if inv_day and inv_day[0] == day:
                inv_day = next(inv_iter, None)
            if sta_day and sta_day[0] == day:
                sta_day = next(station_iter, None)
        with catalog.engine.begin() as conn:
            put(
                conn,
                runs,
                {"run_id": batch_id},
                {
                    "kind": "ingest",
                    "plant_id": plant,
                    "from": start,
                    "to": end,
                    "finished_at": now(),
                    "partitions": len(outcomes),
                },
                org_id=settings.org,
                status="committed",
            )
    except Exception as exc:
        catalog.fail(batch_id, str(exc).split(":")[0][:100])
        raise
    return {
        "batch_id": batch_id,
        "plant_id": plant,
        "partitions": len(outcomes),
        "rows": sum(r["rows"] for r in outcomes),
        "results": outcomes,
    }


def publish_day(
    catalog,
    objects,
    settings,
    plant,
    day,
    version,
    source_info,
    meta,
    bounds,
    inv_rows,
    sta_rows,
    fail_at,
    poa_threshold,
    power_ratio,
):
    started = time.monotonic()
    run_id = str(uuid.uuid4())
    key = {
        "org_id": settings.org,
        "plant_id": plant,
        "partition_id": day,
        "report_timezone": settings.timezone,
        "calculation_version": CALCULATION_VERSION,
    }
    prefix = f"staging/{settings.org}/{plant}/{day}/{run_id}"
    staging = settings.root / prefix
    staging.mkdir(parents=True, exist_ok=False)
    run_payload = dict(key, source_version=version, started_at=now(), source_objects=source_info)
    with catalog.engine.begin() as conn:
        put(conn, runs, {"run_id": run_id}, run_payload, org_id=settings.org, status="running")
    try:
        inv_rows, inv_dupes = deduplicate(inv_rows)
        sta_rows, sta_dupes = deduplicate(sta_rows)
        metric, quality, candidates, series = analyze(
            inv_rows,
            sta_rows,
            meta["nominal_power_kw"],
            bounds,
            day,
            settings.timezone,
            poa_threshold,
            power_ratio,
        )
        if inv_dupes + sta_dupes:
            quality.append(
                {
                    "rule_id": "DQ-DUPLICATE-IDENTICAL",
                    "count": inv_dupes + sta_dupes,
                    "reason": "Identical natural-key duplicates removed",
                    "origin": "input",
                }
            )
        metric.update(
            plant_id=plant, dataset_version=version, calculation_version=CALCULATION_VERSION
        )
        logical_hash = canonical_hash(
            {
                "inverter": inv_rows,
                "station": sta_rows,
                "metric": metric,
                "rules": {
                    "poa": poa_threshold,
                    "ratio": power_ratio,
                    "version": CALCULATION_VERSION,
                },
            }
        )
        for kind, data, source in (
            ("inverter", inv_rows, source_info[1]),
            ("station", sta_rows, source_info[2]),
        ):
            path = staging / (kind + ".parquet")
            write_parquet(path, data, source["source_object_id"], run_id)
            objects.upload(path, prefix + "/" + path.name)
        series_file = staging / "series.json"
        series_file.write_text(json.dumps(series, allow_nan=False), encoding="utf-8")
        series_uri = objects.upload(series_file, prefix + "/series.json")
        manifest = dict(
            key,
            run_id=run_id,
            active_source_version=version,
            object_prefix=prefix,
            logical_content_hash=logical_hash,
            committed_at=now(),
            row_count=len(inv_rows),
            source_objects=source_info,
            series_uri=series_uri,
            thresholds={"poa": poa_threshold, "ratio": power_ratio},
            metadata=meta,
        )
        with catalog.engine.begin() as conn:
            put(
                conn, runs, {"run_id": run_id}, run_payload, org_id=settings.org, status="validated"
            )
        if fail_at == "before_commit":
            raise RuntimeError("INJECTED_BEFORE_COMMIT")
        with catalog.engine.begin() as conn:
            if conn.dialect.name == "postgresql":
                conn.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
                    {"key": json.dumps(key, sort_keys=True)},
                )
            put(conn, metrics, {"run_id": run_id}, metric)
            put(conn, issues, {"run_id": run_id}, {"items": quality})
            put(conn, events, {"run_id": run_id}, {"items": candidates})
            put(conn, active, key, manifest, run_id=run_id)
            if fail_at == "during_commit":
                raise RuntimeError("INJECTED_DURING_COMMIT")
            put(
                conn,
                runs,
                {"run_id": run_id},
                dict(
                    run_payload,
                    finished_at=now(),
                    elapsed_ms=round((time.monotonic() - started) * 1000),
                    rows=len(inv_rows),
                ),
                org_id=settings.org,
                status="committed",
            )
        return {
            "run_id": run_id,
            "day": day,
            "rows": len(inv_rows),
            "logical_hash": logical_hash,
            "estimated_energy_kwh": metric["estimated_energy_kwh"],
        }
    except Exception as exc:
        (staging / "quarantine.json").write_text(
            json.dumps({"error_code": str(exc).split(":")[0], "run_id": run_id}), encoding="utf-8"
        )
        catalog.fail(run_id, str(exc).split(":")[0][:100])
        raise
