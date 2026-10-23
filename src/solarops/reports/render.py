import base64
import csv
import json
import uuid
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from solarops.acquisition.brpvgen import checksum
from solarops.config import CALCULATION_VERSION
from solarops.contracts.dates import month_bounds
from solarops.pipeline import canonical_hash
from solarops.reports.identity import display_scope, selection_key
from solarops.runtime import execution_context, release_info
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, now, put, reports

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape()
)


def build_report(settings, period, plant=None, source_kind=None):
    start, end = month_bounds(period)
    selection = {"plant_id": plant, "source_kind": source_kind}
    identity = selection_key(selection)
    catalog = Catalog(settings)
    generated_at = now()
    snapshot = catalog.snapshot(settings.org, start, end, plant, source_kind)
    if not snapshot:
        raise ValueError("NO_ACTIVE_PARTITIONS")
    report_id = str(uuid.uuid4())
    directory = settings.root / "reports" / settings.org / report_id
    directory.mkdir(parents=True, exist_ok=False)
    manifests = [r["payload"] for r in snapshot]
    # Observation-derived inventory, not confirmed installed/operating equipment.
    # Older manifests did not record it: do not fabricate a count from row totals.
    metrics = [
        dict(
            r["metric"],
            quality_issue_count=len(r["issues"]["items"]),
            source_inverter_count=len(r["payload"]["source_inverter_bounds"])
            if "source_inverter_bounds" in r["payload"]
            else None,
        )
        for r in snapshot
    ]
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
    interpolation_unknown = sum(m["interpolation_unknown_slots"] for m in metrics)
    report = {
        "report_id": report_id,
        "org_id": settings.org,
        "period": period,
        "scope": display_scope(plant, source_kind),
        "selection": selection,
        "generated_at": generated_at,
        "timezone": settings.timezone,
        "calculation_version": CALCULATION_VERSION,
        "release": release_info(),
        "execution": execution_context(),
        "source_manifest_hash": canonical_hash(manifests),
        "source_kinds": sorted({s["source_kind"] for s in sources.values()}),
        "status": "complete" if complete else "partial_period",
        "days": len(metrics),
        "plant_count": len({r["plant_id"] for r in snapshot}),
        "observed_slots": observed,
        "interpolation_unknown_slots": interpolation_unknown,
        "estimated_energy_kwh": round(sum(m["estimated_energy_kwh"] for m in metrics), 3),
        "coverage": sum(m["observed_slots"] for m in metrics) / denominator
        if denominator
        else None,
        "valid_coverage": sum(m["valid_slots"] for m in metrics) / denominator
        if denominator
        else None,
        "interpolation": sum(
            (m["source_interpolation_ratio"] or 0) * m["observed_slots"] for m in metrics
        )
        / observed
        if observed > interpolation_unknown
        else None,
        "metrics": metrics,
        "issues": quality,
        "candidates": candidates,
        "sources": list(sources.values()),
        "partitions": manifests,
        "synthetic": any(s["source_kind"] == "synthetic" for s in sources.values()),
        "public": any(s["source_kind"] == "public" for s in sources.values()),
    }
    html = directory / "report.html"
    report_css = (Path(__file__).parents[1] / "api/static/report.css").read_text(encoding="utf-8")
    font = (Path(__file__).parents[1] / "api/static/fonts/PretendardVariable.woff2").read_bytes()
    font_license = (Path(__file__).parents[1] / "api/static/fonts/OFL.txt").read_text(
        encoding="utf-8"
    )
    report_css = (
        "/* Pretendard 1.3.9.\n" + font_license + "\n*/"
        "@font-face{font-family:Pretendard;font-weight:100 900;font-display:swap;"
        "src:url(data:font/woff2;base64,"
        + base64.b64encode(font).decode("ascii")
        + ") format('woff2')}"
        + report_css
    )
    html.write_text(
        env.get_template("monthly.html").render(report=report, report_css=report_css),
        encoding="utf-8",
    )
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
        selection=selection,
        generated_at=report["generated_at"],
        source_manifest_hash=report["source_manifest_hash"],
        source_kinds=report["source_kinds"],
        calculation_version=report["calculation_version"],
        status=report["status"],
        artifacts=artifacts,
        artifact_sha256={p.name: checksum(p) for p in (html, csv_path, manifest_path)},
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
                "scope": identity,
                "report_timezone": settings.timezone,
            },
            payload,
            update_if=active_reports.c.payload["generated_at"].as_string() <= generated_at,
            report_run_id=report_id,
        )
    return payload
