"""Shared transactional catalog, PostgreSQL in services; SQLite for offline demos."""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    select,
    text,
)

from solarops.config import CALCULATION_VERSION

metadata = MetaData()


def table(name, keys, extra=()):
    return Table(
        name,
        metadata,
        *(Column(k, String, primary_key=True) for k in keys),
        *extra,
        Column("payload", JSON, nullable=False),
    )


sources = table(
    "source_object",
    ["source_object_id"],
    [
        Column("org_id", String, nullable=False),
        Column("sha256", String, nullable=False),
        UniqueConstraint("org_id", "sha256"),
    ],
)
plants = table("dim_plant", ["org_id", "plant_id"])
versions = table("source_version", ["org_id", "plant_id", "source_version"])
runs = table(
    "pipeline_run",
    ["run_id"],
    [Column("org_id", String, nullable=False), Column("status", String, nullable=False)],
)
active = table(
    "active_partition_manifest",
    ["org_id", "plant_id", "partition_id", "report_timezone", "calculation_version"],
    [Column("run_id", String, nullable=False)],
)
metrics = table("daily_plant_metric", ["run_id"])
issues = table("dq_issue", ["run_id"])
events = table("anomaly_event", ["run_id"])
reports = table("report_run", ["report_run_id"], [Column("org_id", String, nullable=False)])
active_reports = table(
    "active_report_manifest",
    ["org_id", "period", "scope", "report_timezone"],
    [Column("report_run_id", String, nullable=False)],
)


def now():
    return datetime.now(UTC).isoformat()


def put(conn, relation, key, payload, **extra):
    values = dict(key, payload=payload, **extra)
    if conn.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    stmt = insert(relation).values(**values)
    conn.execute(
        stmt.on_conflict_do_update(
            index_elements=list(key), set_={k: v for k, v in values.items() if k not in key}
        )
    )


class Catalog:
    def __init__(self, settings):
        self.settings = settings
        kwargs = (
            {"connect_args": {"timeout": 60}} if settings.database_url.startswith("sqlite") else {}
        )
        self.engine = create_engine(settings.database_url, pool_pre_ping=True, **kwargs)
        if self.engine.dialect.name == "sqlite":
            with self.engine.begin() as conn:
                conn.execute(text("PRAGMA journal_mode=WAL"))
        metadata.create_all(self.engine)

    def snapshot(self, org, start=None, end=None, plant=None, source_kind=None):
        # One SELECT is a consistent statement snapshot even during a concurrent commit.
        stmt = (
            select(
                active,
                metrics.c.payload.label("metric"),
                issues.c.payload.label("issues"),
                events.c.payload.label("events"),
            )
            .join(metrics, active.c.run_id == metrics.c.run_id)
            .join(issues, active.c.run_id == issues.c.run_id)
            .join(events, active.c.run_id == events.c.run_id)
            .where(
                active.c.org_id == org,
                active.c.report_timezone == self.settings.timezone,
                active.c.calculation_version == CALCULATION_VERSION,
            )
        )
        if start:
            stmt = stmt.where(active.c.partition_id >= start)
        if end:
            stmt = stmt.where(active.c.partition_id < end)
        if plant:
            stmt = stmt.where(active.c.plant_id == plant)
        with self.engine.connect() as conn:
            result = [
                dict(r)
                for r in conn.execute(
                    stmt.order_by(active.c.plant_id, active.c.partition_id)
                ).mappings()
            ]
        if source_kind:
            result = [
                row
                for row in result
                if row["payload"].get("source_objects")
                and all(s["source_kind"] == source_kind for s in row["payload"]["source_objects"])
            ]
        return result

    def fail(self, run_id, code):
        with self.engine.begin() as conn:
            row = conn.execute(select(runs).where(runs.c.run_id == run_id)).mappings().one()
            put(
                conn,
                runs,
                {"run_id": run_id},
                dict(row["payload"], finished_at=now(), error_code=code),
                org_id=row["org_id"],
                status="failed",
            )
