import json
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select, text

from solarops.config import Settings, identifier
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, plants, reports, runs


def create_app(settings=None):
    settings = settings or Settings()
    catalog = Catalog(settings)
    app = FastAPI(title="SolarOps Audit — local read-only", docs_url="/docs")

    def artifact(uri):
        if uri.startswith("s3://"):
            bucket, key = uri[5:].split("/", 1)
            store = ObjectStore(settings)
            if bucket != store.bucket:
                raise HTTPException(404)
            return store.client.get_object(Bucket=bucket, Key=key)["Body"].read()
        path = Path(uri).resolve()
        if not path.is_relative_to(settings.root.resolve()):
            raise HTTPException(404)
        return path.read_bytes()

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "local-read-only"}

    @app.get("/ready")
    def ready():
        try:
            with catalog.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            store = ObjectStore(settings)
            if store.client:
                store.client.head_bucket(Bucket=store.bucket)
            return {"status": "ready"}
        except Exception:
            raise HTTPException(503, "Storage unavailable") from None

    @app.get("/api/v1/plants")
    def plant_list(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)):
        with catalog.engine.connect() as conn:
            data = conn.execute(
                select(plants)
                .where(plants.c.org_id == settings.org)
                .order_by(plants.c.plant_id)
                .offset(offset)
                .limit(limit)
            ).mappings()
            return {"items": [r["payload"] for r in data], "offset": offset, "limit": limit}

    @app.get("/api/v1/plants/{plant_id}/metrics")
    def plant_metrics(
        plant_id: str,
        start: str = Query("1900-01-01", alias="from"),
        end: str = Query("2200-01-01", alias="to"),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
    ):
        try:
            identifier(plant_id)
        except ValueError:
            raise HTTPException(422, "Invalid plant ID") from None
        data = catalog.snapshot(settings.org, start, end, plant_id)
        return {
            "items": [
                dict(
                    r["metric"],
                    run_id=r["run_id"],
                    logical_hash=r["payload"]["logical_content_hash"],
                )
                for r in data[offset : offset + limit]
            ],
            "total": len(data),
            "offset": offset,
            "limit": limit,
        }

    @app.get("/api/v1/plants/{plant_id}/issues")
    def plant_issues(
        plant_id: str, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
    ):
        data = catalog.snapshot(settings.org, plant=plant_id)
        items = [
            dict(i, local_date=r["partition_id"], run_id=r["run_id"])
            for r in data
            for i in r["issues"]["items"] + r["events"]["items"]
        ]
        return {"items": items[offset : offset + limit], "total": len(items)}

    @app.get("/api/v1/plants/{plant_id}/series")
    def plant_series(plant_id: str, day: str):
        from datetime import date, timedelta

        try:
            end = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        except ValueError:
            raise HTTPException(422, "Expected ISO date") from None
        data = catalog.snapshot(settings.org, day, end, plant_id)
        return {"items": json.loads(artifact(data[0]["payload"]["series_uri"])) if data else []}

    @app.get("/api/v1/runs")
    def run_list(limit: int = Query(50, ge=1, le=200)):
        with catalog.engine.connect() as conn:
            data = conn.execute(
                select(runs).where(runs.c.org_id == settings.org).limit(limit)
            ).mappings()
            return {
                "items": [
                    dict(run_id=r["run_id"], status=r["status"], **r["payload"]) for r in data
                ]
            }

    @app.get("/api/v1/reports")
    def report_list():
        with catalog.engine.connect() as conn:
            data = conn.execute(
                select(active_reports).where(active_reports.c.org_id == settings.org)
            ).mappings()
            return {"items": [r["payload"] for r in data]}

    @app.get("/api/v1/reports/{report_id}")
    def report_info(report_id: UUID):
        with catalog.engine.connect() as conn:
            row = (
                conn.execute(
                    select(reports).where(
                        reports.c.org_id == settings.org, reports.c.report_run_id == str(report_id)
                    )
                )
                .mappings()
                .first()
            )
        if not row:
            raise HTTPException(404, "Report not found")
        return row["payload"]

    @app.get("/reports/{report_id}/{filename}")
    def report_file(report_id: UUID, filename: str):
        if filename not in {"report.html", "metrics.csv", "manifest.json"}:
            raise HTTPException(404)
        info = report_info(report_id)
        media = {
            "report.html": "text/html",
            "metrics.csv": "text/csv",
            "manifest.json": "application/json",
        }
        return Response(artifact(info["artifacts"][filename]), media_type=media[filename])

    @app.get("/", response_class=HTMLResponse)
    def home():
        return (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")

    return app
