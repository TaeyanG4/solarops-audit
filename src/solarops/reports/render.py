import csv
import json
import uuid
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from solarops.config import CALCULATION_VERSION
from solarops.pipeline import canonical_hash
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, now, put, reports

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape()
)


def month_bounds(period):
    first = date.fromisoformat(period + "-01")
    end = date(first.year + (first.month == 12), first.month % 12 + 1, 1)
    return first.isoformat(), end.isoformat()


def build_report(settings, period, plant=None, source_kind=None):
    start, end = month_bounds(period)
    catalog = Catalog(settings)
    snapshot = catalog.snapshot(settings.org, start, end, plant)
    if source_kind:
        snapshot = [
            r
            for r in snapshot
            if all(s["source_kind"] == source_kind for s in r["payload"]["source_objects"])
        ]
    if not snapshot:
        raise ValueError("NO_ACTIVE_PARTITIONS")
    report_id = str(uuid.uuid4())
    directory = settings.root / "reports" / settings.org / report_id
    directory.mkdir(parents=True, exist_ok=False)
    manifests = [r["payload"] for r in snapshot]
    metrics = [r["metric"] for r in snapshot]
    sources = {s["source_object_id"]: s for m in manifests for s in m["source_objects"]}
    expected_days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    complete = all(
        sum(r["plant_id"] == p for r in snapshot) == expected_days
        for p in {r["plant_id"] for r in snapshot}
    )
    quality = [
        dict(q, plant_id=r["plant_id"], local_date=r["partition_id"])
        for r in snapshot
        for q in r["issues"]["items"]
    ]
    candidates = [dict(e, plant_id=r["plant_id"]) for r in snapshot for e in r["events"]["items"]]
    denominator = sum(m["expected_slots"] for m in metrics)
    observed = sum(m["observed_slots"] for m in metrics)
    report = {
        "report_id": report_id,
        "org_id": settings.org,
        "period": period,
        "scope": plant or ("all-" + source_kind if source_kind else "all"),
        "generated_at": now(),
        "timezone": settings.timezone,
        "calculation_version": CALCULATION_VERSION,
        "source_manifest_hash": canonical_hash(manifests),
        "status": "complete" if complete else "partial_period",
        "days": len(metrics),
        "plant_count": len({r["plant_id"] for r in snapshot}),
        "estimated_energy_kwh": round(sum(m["estimated_energy_kwh"] for m in metrics), 3),
        "coverage": sum(m["observed_slots"] for m in metrics) / denominator if denominator else 0,
        "valid_coverage": sum(m["valid_slots"] for m in metrics) / denominator
        if denominator
        else 0,
        "interpolation": sum(
            (m["source_interpolation_ratio"] or 0) * m["observed_slots"] for m in metrics
        )
        / observed
        if observed
        else 0,
        "metrics": metrics,
        "issues": quality,
        "candidates": candidates,
        "sources": list(sources.values()),
        "partitions": manifests,
        "synthetic": any(s["source_kind"] == "synthetic" for s in sources.values()),
        "public": any(s["source_kind"] == "public" for s in sources.values()),
    }
    html = directory / "report.html"
    html.write_text(env.get_template("monthly.html").render(report=report), encoding="utf-8")
    csv_path = directory / "metrics.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(metrics[0]))
        writer.writeheader()
        writer.writerows(metrics)
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    store = ObjectStore(settings)
    artifacts = {
        p.name: store.upload(p, f"reports/{settings.org}/{report_id}/{p.name}")
        for p in (html, csv_path, manifest_path)
    }
    payload = dict(
        report_id=report_id,
        period=period,
        scope=report["scope"],
        generated_at=report["generated_at"],
        source_manifest_hash=report["source_manifest_hash"],
        status=report["status"],
        artifacts=artifacts,
        local_directory=str(directory.resolve()),
    )
    with catalog.engine.begin() as conn:
        put(conn, reports, {"report_run_id": report_id}, payload, org_id=settings.org)
        put(
            conn,
            active_reports,
            {
                "org_id": settings.org,
                "period": period,
                "scope": report["scope"],
                "report_timezone": settings.timezone,
            },
            payload,
            report_run_id=report_id,
        )
    return payload
