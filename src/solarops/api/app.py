import hashlib
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Query
from fastapi import Path as ApiPath
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from solarops import __version__
from solarops.api.readmodels import available_periods, fleet_overview, run_history
from solarops.config import Settings
from solarops.contracts.dates import date_bounds, month_bounds, next_day
from solarops.diagnostics import inspect_runs
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog, active_reports, metadata, plants, reports, runs

PlantId = Annotated[str, ApiPath(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")]


def create_app(settings=None):
    settings = settings or Settings()
    catalog = Catalog(settings, read_only=True)

    @asynccontextmanager
    async def lifespan(app):
        yield
        catalog.engine.dispose()

    app = FastAPI(
        title="SolarOps Audit — local read-only",
        version=__version__,
        docs_url="/docs",
        lifespan=lifespan,
    )

    @app.exception_handler(SQLAlchemyError)
    async def database_unavailable(request, exc):
        return JSONResponse(
            status_code=503,
            content={"detail": "Catalog unavailable; initialize or restore storage first"},
        )

    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.get("/api/v1/overview")
    def overview(
        period: str = Query(pattern=r"^\d{4}-\d{2}$"),
        source_kind: Literal["public", "synthetic"] | None = None,
    ):
        try:
            return fleet_overview(catalog, period, source_kind)
        except ValueError:
            raise HTTPException(422, "Expected a valid YYYY-MM period") from None

    @app.get("/api/v1/periods")
    def period_list(source_kind: Literal["public", "synthetic"] | None = None):
        return available_periods(catalog, source_kind)

    def artifact(uri, expected_sha256=None):
        try:
            if uri.startswith("s3://"):
                bucket, key = uri[5:].split("/", 1)
                store = ObjectStore(settings, initialize=False)
                if bucket != store.bucket or not store.client:
                    raise HTTPException(404, "Artifact not found")
                body = store.client.get_object(Bucket=bucket, Key=key)["Body"]
                try:
                    data = body.read()
                finally:
                    body.close()
            else:
                path = Path(uri).resolve()
                if not path.is_relative_to(settings.root.resolve()):
                    raise HTTPException(404, "Artifact not found")
                data = path.read_bytes()
        except FileNotFoundError:
            raise HTTPException(404, "Artifact not found") from None
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                raise HTTPException(404, "Artifact not found") from None
            raise HTTPException(503, "Artifact storage unavailable") from None
        except (OSError, BotoCoreError, KeyError, ValueError):
            raise HTTPException(503, "Artifact storage unavailable") from None
        if expected_sha256 and hashlib.sha256(data).hexdigest() != expected_sha256:
            raise HTTPException(503, "Artifact integrity check failed")
        return data

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "local-read-only", "version": __version__}

    @app.get("/ready")
    def ready():
        try:
            with catalog.engine.connect() as conn:
                for relation in metadata.sorted_tables:
                    conn.execute(select(relation).limit(0))
            store = ObjectStore(settings, initialize=False)
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
        plant_id: PlantId,
        start: str = Query("1900-01-01", alias="from"),
        end: str = Query("2200-01-01", alias="to"),
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
    ):
        try:
            date_bounds(start, end)
        except ValueError:
            raise HTTPException(
                422, "Expected YYYY-MM-DD dates with from < to (exclusive)"
            ) from None
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
        plant_id: PlantId, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
    ):
        data = catalog.snapshot(settings.org, plant=plant_id)
        items = [
            dict(i, local_date=r["partition_id"], run_id=r["run_id"])
            for r in data
            for i in r["issues"]["items"] + r["events"]["items"]
        ]
        return {"items": items[offset : offset + limit], "total": len(items)}

    @app.get("/api/v1/plants/{plant_id}/series")
    def plant_series(plant_id: PlantId, day: str):
        try:
            end = next_day(day)
        except ValueError:
            raise HTTPException(422, "Expected YYYY-MM-DD with a representable next day") from None
        data = catalog.snapshot(settings.org, day, end, plant_id)
        if not data:
            return {"items": []}
        payload = data[0]["payload"]
        try:
            items = json.loads(artifact(payload["series_uri"], payload.get("series_sha256")))
        except (ValueError, UnicodeError):
            raise HTTPException(503, "Series artifact invalid") from None
        if not isinstance(items, list):
            raise HTTPException(503, "Series artifact invalid")
        return {"items": items}

    @app.get("/api/v1/runs")
    def run_list(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        level: Literal["all", "batch", "partition"] = "all",
        status: Literal["running", "validated", "committed", "failed"] | None = None,
        plant: str | None = Query(None, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$"),
    ):
        return run_history(catalog, level, status, plant, offset, limit)

    @app.get("/api/v1/runs/{run_id}/diagnostics")
    def run_diagnostics(run_id: UUID, older_than_minutes: int = Query(60, ge=1, le=525600)):
        try:
            result = inspect_runs(settings, older_than_minutes, limit=1, run_id=str(run_id))
        except ValueError:
            raise HTTPException(503, "Catalog unavailable") from None
        if result["item"] is None:
            raise HTTPException(404, "Run not found")
        return result

    @app.get("/api/v1/runs/{run_id}")
    def run_detail(run_id: UUID):
        with catalog.engine.connect() as conn:
            row = (
                conn.execute(
                    select(runs).where(runs.c.org_id == settings.org, runs.c.run_id == str(run_id))
                )
                .mappings()
                .first()
            )
            if not row:
                raise HTTPException(404, "Run not found")
            children = conn.execute(
                select(runs)
                .where(
                    runs.c.org_id == settings.org,
                    runs.c.payload["batch_id"].as_string() == str(run_id),
                )
                .order_by(runs.c.payload["partition_id"].as_string())
                .limit(500)
            ).mappings()
            return dict(
                row["payload"],
                run_id=row["run_id"],
                status=row["status"],
                partitions=[
                    dict(r["payload"], run_id=r["run_id"], status=r["status"]) for r in children
                ],
            )

    @app.get("/api/v1/reports")
    def report_list(
        period: str | None = None,
        source_kind: Literal["public", "synthetic"] | None = None,
    ):
        if period is not None:
            try:
                month_bounds(period)
            except ValueError:
                raise HTTPException(422, "Expected a valid YYYY-MM period") from None
        statement = select(active_reports).where(
            active_reports.c.org_id == settings.org,
            active_reports.c.report_timezone == settings.timezone,
        )
        if period is not None:
            statement = statement.where(active_reports.c.period == period)
        with catalog.engine.connect() as conn:
            payloads = [dict(r["payload"]) for r in conn.execute(statement).mappings()]
        items = []
        for payload in payloads:
            if "source_kinds" not in payload:
                # Older reports retain their source evidence in the immutable manifest.
                # Never infer provenance from plant names or rewrite historical artifacts.
                try:
                    manifest = json.loads(
                        artifact(
                            payload["artifacts"]["manifest.json"],
                            payload.get("artifact_sha256", {}).get("manifest.json"),
                        )
                    )
                    payload["source_kinds"] = sorted(
                        {source["source_kind"] for source in manifest["sources"]}
                    )
                except (
                    OSError,
                    ValueError,
                    KeyError,
                    TypeError,
                    BotoCoreError,
                    ClientError,
                    HTTPException,
                ):
                    payload["source_kinds"] = None
            payload["source_metadata_status"] = (
                "available" if payload["source_kinds"] else "unavailable"
            )
            if source_kind is None or source_kind in (payload["source_kinds"] or []):
                items.append(payload)
        return {"items": items}

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
        return Response(
            artifact(info["artifacts"][filename], info.get("artifact_sha256", {}).get(filename)),
            media_type=media[filename],
        )

    @app.get("/", response_class=HTMLResponse)
    def home():
        return (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")

    return app
