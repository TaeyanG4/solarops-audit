"""Bounded ONS monthly snapshots, with atomic incremental daily publication.

The official dictionary does not specify timezone or interval anchor. Preserve
source-native hourly timestamps and MWmed; do not feed these into energy-v2.
"""

import calendar
import csv
import hashlib
import json
import math
import re
import urllib.error
import urllib.request
import uuid
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, literal, select, update

from solarops.acquisition.brpvgen import checksum
from solarops.runtime import execution_context, release_info
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import (
    Catalog,
    claim,
    collection_cursors,
    collection_partitions,
    collection_runs,
    now,
    put,
)

SOURCE = "ons-generation-hourly"
API = "https://dados.ons.org.br/api/3/action/package_show?id=geracao-usina-2"
BASE = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/"
CONTRACT = {
    "source_id": SOURCE,
    "adapter_version": "ons-hourly-v1",
    "dataset_url": "https://dados.ons.org.br/dataset/geracao-usina-2",
    "dictionary_url": BASE + "DicionarioDados_GeracaoPorUsina.pdf",
    "license_id": "cc-by",
    "license_url": "http://www.opendefinition.org/licenses/cc-by",
    "license_version": "unspecified",
    "unit": "MWmed",
    "timezone": "unspecified",
    "interval_anchor": "unspecified",
    "energy_conversion": False,
    "interpolation_and_sample_counts": "not provided by source",
}
FIELDS = (
    "din_instante id_subsistema nom_subsistema id_estado nom_estado "
    "cod_modalidadeoperacao nom_tipousina nom_tipocombustivel nom_usina id_ons ceg val_geracao"
).split()
VERIFIED = {"TIPO I", "TIPO II-A", "TIPO II-B", "TIPO II-C", "Conjunto de Usinas"}


def month(value):
    if not re.fullmatch(r"20\d{2}-(0[1-9]|1[0-2])", value) or value < "2022-01":
        raise ValueError("ONS_MONTH: expected YYYY-MM from 2022-01")
    return value


def source_url(period):
    return BASE + "GERACAO_USINA-2_" + month(period).replace("-", "_") + ".csv"


def encoded(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def download(url, path, etag=None, max_bytes=256 * 1024**2):
    """No arbitrary input URLs; partial responses never become successful snapshots."""
    headers = {"User-Agent": "SolarOps-Audit/ONS", "Accept-Encoding": "identity"}
    if etag:
        headers["If-None-Match"] = etag
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90)
    except urllib.error.HTTPError as exc:
        if exc.code == 304 and etag:
            return {"not_modified": True, "etag": etag}
        raise
    with response, path.open("xb") as out:
        if response.status != 200 or response.headers.get("Content-Range"):
            raise ValueError("ONS_INCOMPLETE_HTTP_RESPONSE")
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise ValueError("ONS_DOWNLOAD_LIMIT")
        total = 0
        while chunk := response.read(1024**2):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("ONS_DOWNLOAD_LIMIT")
            out.write(chunk)
        if not total or (length and total != int(length)):
            raise ValueError("ONS_INCOMPLETE_HTTP_RESPONSE")
        return {"not_modified": False, "etag": response.headers.get("ETag"), "bytes": total}


def parse(path, period):
    """Keep invalid readings explicitly null; conflicting duplicate identities abort."""
    month(period)
    days, duplicates = defaultdict(dict), Counter()
    input_rows = 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames != FIELDS:
            raise ValueError("ONS_SCHEMA_CHANGED")
        for raw in reader:
            input_rows += 1
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError("ONS_INCOMPLETE_ROW")
            stamp = raw["din_instante"]
            try:
                parsed = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("ONS_TIMESTAMP") from None
            if (
                parsed.strftime("%Y-%m-%d %H:%M:%S") != stamp
                or stamp[:7] != period
                or parsed.minute
                or parsed.second
            ):
                raise ValueError("ONS_TIMESTAMP")
            if raw["nom_tipousina"] != "FOTOVOLTAICA":
                continue
            mode = raw["cod_modalidadeoperacao"]
            basis = (
                "verified"
                if mode in VERIFIED
                else ("forecast" if mode == "Pequenas Usinas (Tipo III)" else "unspecified")
            )
            if (
                not raw["nom_usina"]
                or not raw["id_estado"]
                or (basis == "verified" and not raw["id_ons"])
            ):
                raise ValueError("ONS_ENTITY_ID")
            # Group names are only source-local composite identifiers, never plant IDs.
            identity = (
                [raw["id_ons"]]
                if raw["id_ons"]
                else [
                    raw[k]
                    for k in (
                        "id_subsistema",
                        "id_estado",
                        "cod_modalidadeoperacao",
                        "nom_usina",
                        "ceg",
                    )
                ]
            )
            entity = ("ons:" if raw["id_ons"] else "group:") + hashlib.sha256(
                encoded(identity)
            ).hexdigest()
            try:
                value = float(raw["val_geracao"])
                valid = math.isfinite(value) and value >= 0
            except ValueError:
                value, valid = None, False
            row = {
                "source_time": stamp,
                "ts_utc": None,
                "entity_id": entity,
                "generation_mwmed": value if valid else None,
                "valid": valid,
                "generation_basis": basis,
                "source": raw,
            }
            day, key = stamp[:10], (entity, stamp)
            if key in days[day]:
                if days[day][key] != row:
                    raise ValueError("ONS_DUPLICATE_CONFLICT")
                duplicates[day] += 1
            else:
                days[day][key] = row
    if not days:
        raise ValueError("ONS_EMPTY_PHOTOVOLTAIC_SNAPSHOT")
    result = {}
    for day, by_key in sorted(days.items()):
        rows = [by_key[key] for key in sorted(by_key)]
        # Coverage is per entity present that day, not a claim about the whole fleet.
        entities = len({r["entity_id"] for r in rows})
        payload = {
            "state": "available",
            "rows": len(rows),
            "entities": entities,
            "invalid_values": sum(not r["valid"] for r in rows),
            "duplicate_rows": duplicates[day],
            "missing_hour_labels_present_entities": entities * 24 - len(rows),
            "generation_basis_counts": dict(Counter(r["generation_basis"] for r in rows)),
        }
        content = encoded({"contract": CONTRACT, "quality": payload, "items": rows})
        result[day] = (hashlib.sha256(content).hexdigest(), content, payload)
    return result, input_rows


def cursor(catalog, period):
    with catalog.engine.connect() as conn:
        return conn.execute(
            select(collection_cursors.c.payload).where(
                collection_cursors.c.org_id == catalog.settings.org,
                collection_cursors.c.source_id == SOURCE,
                collection_cursors.c.period == month(period),
            )
        ).scalar_one_or_none()


def publish(catalog, store, path, period, expected, run_id, provenance, fail_at=None):
    """Upload immutable artifacts first, atomically switch changed days and cursor."""
    org = catalog.settings.org
    digest = checksum(path)
    raw_uri = store.raw(path, org, digest)
    previous = status(catalog, period)["partitions"]
    previous = {p["day"]: p for p in previous}
    parsed, input_rows = parse(store.raw_path(org, digest, path.name), period)
    manifests, changed = {}, []
    for day in sorted(set(parsed) | set(previous)):
        if day in parsed:
            logical_hash, content, quality = parsed[day]
        else:
            quality = {"state": "withdrawn", "rows": 0}
            content = encoded({"contract": CONTRACT, "quality": quality, "items": []})
            logical_hash = hashlib.sha256(content).hexdigest()
        if previous.get(day, {}).get("logical_hash") == logical_hash:
            continue
        artifact = catalog.settings.root / "staging" / org / run_id / (day + ".json")
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(content)
        uri = store.upload(artifact, f"normalized/{org}/{SOURCE}/{run_id}/{day}.json")
        manifests[day] = {
            **quality,
            "day": day,
            "run_id": run_id,
            "logical_hash": logical_hash,
            "artifact_sha256": hashlib.sha256(content).hexdigest(),
            "artifact_uri": uri,
            "raw_uri": raw_uri,
            "raw_sha256": digest,
            "provenance": provenance,
        }
        changed.append(day)
    next_cursor = {
        **CONTRACT,
        "period": period,
        "run_id": run_id,
        "checked_at": now(),
        "raw_sha256": digest,
        "raw_uri": raw_uri,
        "etag": provenance.get("etag"),
        "provenance": provenance,
        "input_rows": input_rows,
        "photovoltaic_rows": sum(v[2]["rows"] for v in parsed.values()),
        "changed_days": changed,
    }
    commit(catalog, period, expected, next_cursor, manifests, fail_at)
    return next_cursor


def commit(catalog, period, expected, next_cursor, manifests, fail_at=None):
    key = {"org_id": catalog.settings.org, "source_id": SOURCE, "period": period}
    with catalog.engine.begin() as conn:
        if expected is None:
            won = claim(conn, collection_cursors, key, next_cursor)
        else:
            won = (
                conn.execute(
                    update(collection_cursors)
                    .where(
                        *(collection_cursors.c[k] == v for k, v in key.items()),
                        collection_cursors.c.payload["run_id"].as_string() == expected["run_id"],
                    )
                    .values(payload=next_cursor)
                    .returning(literal(1))
                ).scalar_one_or_none()
                == 1
            )
        if not won:
            raise ValueError("ONS_CURSOR_CONFLICT: retry from latest successful snapshot")
        for day, payload in manifests.items():
            put(
                conn,
                collection_partitions,
                {
                    "org_id": catalog.settings.org,
                    "source_id": SOURCE,
                    "day": day,
                },
                payload,
            )
        if fail_at == "during_commit":
            raise RuntimeError("ONS_TEST_PUBLICATION_FAILURE")
        put(
            conn,
            collection_runs,
            {"org_id": catalog.settings.org, "run_id": next_cursor["run_id"]},
            {
                **next_cursor,
                "status": "committed",
                "execution": execution_context(),
                "release": release_info(),
            },
        )


def sync_month(settings, period):
    month(period)
    catalog, store = Catalog(settings), ObjectStore(settings)
    run_id = str(uuid.uuid4())
    staging = settings.root / "staging" / settings.org / run_id
    staging.mkdir(parents=True, exist_ok=False)
    expected = cursor(catalog, period)
    record = {
        "source_id": SOURCE,
        "period": period,
        "status": "running",
        "started_at": now(),
        "execution": execution_context(),
        "release": release_info(),
    }
    try:
        with catalog.engine.begin() as conn:
            put(conn, collection_runs, {"org_id": settings.org, "run_id": run_id}, record)
        metadata_path = staging / "metadata.json"
        download(API, metadata_path, max_bytes=8 * 1024**2)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        package = metadata["result"]
        url = source_url(period)
        if (
            not metadata.get("success")
            or package.get("license_id") != "cc-by"
            or not any(r.get("url") == url for r in package["resources"])
        ):
            raise ValueError("ONS_SOURCE_CONTRACT_CHANGED")
        metadata_sha = checksum(metadata_path)
        metadata_uri = store.raw(metadata_path, settings.org, metadata_sha)
        path = staging / Path(url).name
        response = download(url, path, (expected or {}).get("etag"))
        provenance = {
            "source_url": url,
            "metadata_uri": metadata_uri,
            "metadata_sha256": metadata_sha,
            "metadata_modified": package.get("metadata_modified"),
            "license_id": package["license_id"],
            "license_url": package.get("license_url"),
            "etag": response.get("etag"),
            "fetched_at": now(),
        }
        if response["not_modified"] or (expected and checksum(path) == expected["raw_sha256"]):
            result = {
                **expected,
                "run_id": run_id,
                "checked_at": now(),
                "changed_days": [],
                "provenance": provenance,
                "etag": response.get("etag"),
            }
            commit(catalog, period, expected, result, {})
        else:
            result = publish(catalog, store, path, period, expected, run_id, provenance)
        return result
    except Exception as exc:
        with catalog.engine.begin() as conn:
            put(
                conn,
                collection_runs,
                {"org_id": settings.org, "run_id": run_id},
                {
                    **record,
                    "status": "failed",
                    "finished_at": now(),
                    "error_code": type(exc).__name__,
                },
            )
        raise
    finally:
        catalog.engine.dispose()


def sync(settings, period=None, as_of=None):
    if period and as_of:
        raise ValueError("Choose --period or --as-of")
    if period:
        periods = [month(period)]
    else:
        day = date.fromisoformat(as_of) if as_of else datetime.now(UTC).date()
        periods = [
            (day.replace(day=1) - timedelta(days=1)).strftime("%Y-%m"),
            day.strftime("%Y-%m"),
        ]
    return {"source_id": SOURCE, "months": [sync_month(settings, p) for p in periods]}


def status(catalog, period):
    month(period)
    last = calendar.monthrange(int(period[:4]), int(period[5:]))[1]
    with catalog.engine.connect() as conn:
        success = conn.execute(
            select(collection_cursors.c.payload).where(
                collection_cursors.c.org_id == catalog.settings.org,
                collection_cursors.c.source_id == SOURCE,
                collection_cursors.c.period == period,
            )
        ).scalar_one_or_none()
        # Include failed-only months, without exposing other organizations or DSNs.
        periods = (
            conn.execute(
                select(collection_cursors.c.period)
                .where(
                    collection_cursors.c.org_id == catalog.settings.org,
                    collection_cursors.c.source_id == SOURCE,
                )
                .union(
                    select(collection_runs.c.payload["period"].as_string()).where(
                        collection_runs.c.org_id == catalog.settings.org,
                        collection_runs.c.payload["source_id"].as_string() == SOURCE,
                    )
                )
            )
            .scalars()
            .all()
        )
        partitions = (
            conn.execute(
                select(collection_partitions.c.payload)
                .where(
                    collection_partitions.c.org_id == catalog.settings.org,
                    collection_partitions.c.source_id == SOURCE,
                    collection_partitions.c.day >= period + "-01",
                    collection_partitions.c.day <= f"{period}-{last:02d}",
                )
                .order_by(collection_partitions.c.day)
            )
            .scalars()
            .all()
        )
        attempts = (
            conn.execute(
                select(collection_runs.c.payload)
                .where(
                    collection_runs.c.org_id == catalog.settings.org,
                    collection_runs.c.payload["source_id"].as_string() == SOURCE,
                    collection_runs.c.payload["period"].as_string() == period,
                )
                .order_by(
                    func.coalesce(
                        collection_runs.c.payload["checked_at"].as_string(),
                        collection_runs.c.payload["finished_at"].as_string(),
                        collection_runs.c.payload["started_at"].as_string(),
                    ).desc()
                )
                .limit(20)
            )
            .scalars()
            .all()
        )
    return {
        "contract": CONTRACT,
        "period": period,
        "partitions": partitions,
        "recent_attempts": attempts,
        "last_success": success,
        "available_periods": sorted((p for p in periods if p), reverse=True),
        "storage": {
            "environment": catalog.settings.environment
            if catalog.settings.environment in {"compose", "kubernetes", "native"}
            else "unspecified",
            "catalog": catalog.engine.dialect.name,
            "objects": "s3" if catalog.settings.s3_endpoint else "filesystem",
            "org": catalog.settings.org,
            "scheduler_status": "not_observed",
        },
    }
