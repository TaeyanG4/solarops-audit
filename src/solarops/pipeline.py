import hashlib
import itertools
import json
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import duckdb
from sqlalchemy import select, text, update

from solarops.acquisition.brpvgen import DOI, checksum
from solarops.analytics.metrics import analyze, day_window
from solarops.config import CALCULATION_VERSION, identifier
from solarops.contracts.brpvgen import failure_code, read_metadata
from solarops.normalize.parquet import (
    configure_duckdb,
    inverter_id,
    normalize,
    rows,
    sql_quote,
    timestamp_utc,
    write_parquet,
)
from solarops.runtime import execution_context, failure_recording, release_info
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import (
    Catalog,
    active,
    claim,
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
    result, identities = {}, {}
    with duckdb.connect() as conn:
        configure_duckdb(conn)
        q = f"read_csv({sql_quote(path)}, all_varchar=true)"
        unknown = {r[0] for r in conn.execute(f"SELECT DISTINCT ps_id FROM {q}").fetchall()} - set(
            metadata_ids
        )
        if unknown:
            raise ValueError("UNKNOWN_PLANT_IN_SOURCE")
        cursor = conn.execute(
            f"SELECT inverter_id, datetime FROM {q} WHERE ps_id=?",
            [plant],
        )
        # Validate every contributing row, including rows outside the request window.
        # Bounded batches avoid materializing the file or accepting SQL's naive UTC cast.
        while batch := cursor.fetchmany(2048):
            for raw_id, raw_time in batch:
                if raw_id not in identities:
                    identities[raw_id] = inverter_id(raw_id)
                inv, stamp = identities[raw_id], timestamp_utc(raw_time)
                left, right = result.get(inv, (stamp, stamp))
                result[inv] = (min(left, stamp), max(right, stamp))
    return result


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
    restore=False,
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
    source_info = []
    captured = {}
    for kind, path in (
        ("metadata", metadata_path),
        ("inverter", inverter_path),
        ("station", station_path),
    ):
        digest = checksum(path)
        sid = str(uuid.uuid5(uuid.NAMESPACE_URL, settings.org + ":" + digest))
        uri = objects.raw(path, settings.org, digest)
        captured[kind] = objects.raw_path(settings.org, digest, path.name)
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
        source_info.append(info)
    # Every parser uses the preserved bytes whose digest was recorded above.
    meta = read_metadata(captured["metadata"])
    if plant not in meta:
        raise ValueError("UNKNOWN_PLANT")
    with catalog.engine.begin() as conn:
        for info in source_info:
            claim(
                conn,
                sources,
                {"source_object_id": info["source_object_id"]},
                info,
                org_id=settings.org,
                sha256=info["sha256"],
            )
    fingerprint = canonical_hash([s["sha256"] for s in source_info])
    version_key = {"org_id": settings.org, "plant_id": plant, "source_version": source_version}
    with catalog.engine.begin() as conn:
        claim(
            conn, versions, version_key, {"fingerprint": fingerprint, "source_objects": source_info}
        )
        existing = conn.execute(select(versions).filter_by(**version_key)).mappings().first()
        if existing and existing["payload"]["fingerprint"] != fingerprint:
            raise ValueError("SOURCE_VERSION_CONFLICT: use a new explicit version")
    # Capture expected publications before any daily work. A slow batch cannot
    # overwrite a publication that appeared while it was normalizing/uploading.
    with catalog.engine.connect() as conn:
        expected = {
            row["partition_id"]: row
            for row in conn.execute(
                select(active).where(
                    active.c.org_id == settings.org,
                    active.c.plant_id == plant,
                    active.c.report_timezone == settings.timezone,
                    active.c.calculation_version == CALCULATION_VERSION,
                    active.c.partition_id >= start,
                    active.c.partition_id < end,
                )
            ).mappings()
        }
        expected_metadata = conn.execute(
            select(plants.c.payload).filter_by(org_id=settings.org, plant_id=plant)
        ).scalar_one_or_none()
        # Includes pre-upgrade history; source-version names have no ordering.
        prior_days = set(
            conn.execute(
                select(runs.c.payload["partition_id"].as_string()).where(
                    runs.c.org_id == settings.org,
                    runs.c.status == "committed",
                    runs.c.payload["plant_id"].as_string() == plant,
                    runs.c.payload["source_version"].as_string() == source_version,
                    runs.c.payload["report_timezone"].as_string() == settings.timezone,
                    runs.c.payload["calculation_version"].as_string() == CALCULATION_VERSION,
                    runs.c.payload["partition_id"].as_string() >= start,
                    runs.c.payload["partition_id"].as_string() < end,
                )
            ).scalars()
        )
    if not restore and any(
        day in prior_days and row["payload"]["active_source_version"] != source_version
        for day, row in expected.items()
    ):
        raise ValueError("HISTORICAL_RESTORE_REQUIRES_FLAG: use --restore for intentional rollback")
    batch_id = str(uuid.uuid4())
    batch_started = time.monotonic()
    batch_payload = {
        "kind": "ingest",
        "plant_id": plant,
        "from": start,
        "to": end,
        "started_at": now(),
        "source_version": source_version,
        "source_kind": source_kind,
        "report_timezone": settings.timezone,
        "calculation_version": CALCULATION_VERSION,
        "restore_requested": restore,
        "release": release_info(),
        "execution": execution_context(),
        "stage": "processing_partitions",
    }
    with catalog.engine.begin() as conn:
        put(
            conn,
            runs,
            {"run_id": batch_id},
            batch_payload,
            org_id=settings.org,
            status="running",
        )
    outcomes = []
    try:
        bounds = source_bounds(captured["inverter"], plant, meta)
        # BR versions are bounded upserts, not authoritative withdrawal snapshots.
        # Never report a successful correction while silently keeping an old day
        # inside the request that the new source no longer covers.
        for day in expected:
            day_start, day_end = day_window(day, settings.timezone)
            if not any(a < day_end and b >= day_start for a, b in bounds.values()):
                raise ValueError("SOURCE_RANGE_SHRINK: existing day outside new source bounds")
        inv_iter = iter(
            normalized_days(
                captured["inverter"], "inverter", plant, begin_utc, end_utc, settings.timezone
            )
        )
        station_iter = iter(
            normalized_days(
                captured["station"], "station", plant, begin_utc, end_utc, settings.timezone
            )
        )
        inv_day, sta_day = next(inv_iter, None), next(station_iter, None)
        for offset in range((right - left).days):
            day = (left + timedelta(days=offset)).isoformat()
            inv_rows = inv_day[1] if inv_day and inv_day[0] == day else []
            sta_rows = sta_day[1] if sta_day and sta_day[0] == day else []
            day_start, day_end = day_window(day, settings.timezone)
            # Outside observed source bounds, do not invent expected coverage.
            if inv_rows or any(a < day_end and b >= day_start for a, b in bounds.values()):
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
                        batch_id=batch_id,
                        expected_run_id=expected[day]["run_id"] if day in expected else None,
                        expected_metadata=expected_metadata,
                        restore=restore,
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
                    **batch_payload,
                    "finished_at": now(),
                    "partitions": len(outcomes),
                    "rows": sum(r["rows"] for r in outcomes),
                    "elapsed_ms": round((time.monotonic() - batch_started) * 1000),
                    "stage": "complete",
                },
                org_id=settings.org,
                status="committed",
            )
    except Exception as exc:
        with failure_recording(batch_id, failure_code(exc), "batch_catalog"):
            catalog.fail(batch_id, failure_code(exc))
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
    batch_id=None,
    expected_run_id=None,
    expected_metadata=None,
    restore=False,
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
    run_payload = dict(
        key,
        kind="partition",
        batch_id=batch_id,
        source_version=version,
        started_at=now(),
        source_objects=source_info,
        expected_run_id=expected_run_id,
        restore_requested=restore,
        release=release_info(),
        execution=execution_context(),
        stage="analyzing",
    )
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
                "quality": quality,
                "candidates": candidates,
                "series": series,
                "rules": {
                    "poa": poa_threshold,
                    "ratio": power_ratio,
                    "version": CALCULATION_VERSION,
                },
            }
        )
        run_payload.update(stage="uploading", rows=len(inv_rows), station_rows=len(sta_rows))
        with catalog.engine.begin() as conn:
            put(conn, runs, {"run_id": run_id}, run_payload, org_id=settings.org, status="running")
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
        day_start, day_end = day_window(day, settings.timezone)
        manifest = dict(
            key,
            run_id=run_id,
            active_source_version=version,
            object_prefix=prefix,
            logical_content_hash=logical_hash,
            committed_at=now(),
            row_count=len(inv_rows),
            source_inverter_bounds={
                str(inv): {"start_utc": first.isoformat(), "last_observed_utc": last.isoformat()}
                for inv, (first, last) in sorted(bounds.items())
                if first < day_end and last >= day_start
            },
            source_objects=source_info,
            series_uri=series_uri,
            series_sha256=checksum(series_file),
            thresholds={"poa": poa_threshold, "ratio": power_ratio},
            metadata=meta,
            previous_run_id=expected_run_id,
            restore_requested=restore,
            release=release_info(),
            execution=execution_context(),
        )
        run_payload["stage"] = "publishing"
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
                    {"key": json.dumps([settings.org, plant])},
                )
            put(conn, metrics, {"run_id": run_id}, metric)
            put(conn, issues, {"run_id": run_id}, {"items": quality})
            put(conn, events, {"run_id": run_id}, {"items": candidates})
            if expected_run_id is None:
                changed = claim(conn, active, key, manifest, run_id=run_id)
            else:
                changed = (
                    conn.execute(
                        update(active)
                        .filter_by(**key)
                        .where(active.c.run_id == expected_run_id)
                        .values(payload=manifest, run_id=run_id)
                        .returning(active.c.run_id)
                    ).scalar_one_or_none()
                    == run_id
                )
            if not changed:
                raise ValueError("PUBLICATION_CONFLICT: active changed; inspect and retry")
            # PG serializes per plant; preceding writes serialize SQLite writers.
            # Metadata and daily publication are committed in the same transaction.
            plant_key = {"org_id": settings.org, "plant_id": plant}
            current_metadata = conn.execute(
                select(plants.c.payload).filter_by(**plant_key)
            ).scalar_one_or_none()
            if current_metadata not in (expected_metadata, meta):
                raise ValueError("PLANT_METADATA_CONFLICT: metadata changed; inspect and retry")
            put(conn, plants, plant_key, meta)
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
                    stage="complete",
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
        with failure_recording(run_id, failure_code(exc), "quarantine"):
            (staging / "quarantine.json").write_text(
                json.dumps({"error_code": failure_code(exc), "run_id": run_id}), encoding="utf-8"
            )
        with failure_recording(run_id, failure_code(exc), "partition_catalog"):
            catalog.fail(run_id, failure_code(exc))
        raise
