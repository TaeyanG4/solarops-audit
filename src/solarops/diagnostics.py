"""Read-only evidence for unfinished runs; age never proves a process has died."""

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url

from solarops.storage.postgres import active, runs


def inspect_runs(settings, older_than_minutes=60, limit=100, offset=0, at=None, *, run_id=None):
    if not 1 <= older_than_minutes <= 525600 or not 1 <= limit <= 500 or offset < 0:
        raise ValueError("Use minutes 1..525600, limit 1..500 and offset >= 0")
    at = at or datetime.now(UTC)
    if at.tzinfo is None:
        raise ValueError("Inspection time must include a timezone")
    url = make_url(settings.database_url)
    if url.get_backend_name() == "sqlite":
        if not url.database or url.database == ":memory:":
            raise ValueError("Inspection requires an existing database file")
        database = Path(url.database).resolve()
        if not database.is_file():
            raise ValueError("Inspection requires an existing database file")
        url = url.set(database=database.as_uri(), query={**url.query, "mode": "ro", "uri": "true"})
    options = {"postgresql_readonly": True} if url.get_backend_name() == "postgresql" else {}
    engine = create_engine(url, pool_pre_ping=True, execution_options=options)
    pending = (
        runs.c.org_id == settings.org,
        runs.c.run_id == run_id if run_id else runs.c.status.in_(["running", "validated"]),
    )
    try:
        with engine.connect() as conn:
            total = conn.execute(
                select(func.count()).select_from(runs).where(*pending)
            ).scalar_one()
            rows = (
                conn.execute(
                    select(runs)
                    .where(*pending)
                    .order_by(
                        func.coalesce(runs.c.payload["started_at"].as_string(), ""), runs.c.run_id
                    )
                    .offset(offset)
                    .limit(limit)
                )
                .mappings()
                .all()
            )
            ids = [r["run_id"] for r in rows]
            published = dict(
                conn.execute(
                    select(active.c.run_id, func.count())
                    .where(active.c.org_id == settings.org, active.c.run_id.in_(ids))
                    .group_by(active.c.run_id)
                ).all()
            )
            batch = runs.c.payload["batch_id"].as_string()
            child_counts = conn.execute(
                select(batch, runs.c.status, func.count())
                .where(runs.c.org_id == settings.org, batch.in_(ids))
                .group_by(batch, runs.c.status)
            ).all()
            active_children = dict(
                conn.execute(
                    select(batch, func.count())
                    .select_from(runs)
                    .join(active, active.c.run_id == runs.c.run_id)
                    .where(
                        runs.c.org_id == settings.org,
                        active.c.org_id == settings.org,
                        batch.in_(ids),
                    )
                    .group_by(batch)
                ).all()
            )
            current_result, lookup_complete = None, False
            if run_id and rows:
                payload = rows[0]["payload"]
                scope = ("plant_id", "partition_id", "report_timezone", "calculation_version")
                lookup_complete = all(payload.get(key) for key in scope)
                if lookup_complete:
                    current = conn.execute(
                        select(active.c.run_id)
                        .where(active.c.org_id == settings.org)
                        .where(*(active.c[key] == payload[key] for key in scope))
                    ).scalar_one_or_none()
                    if current:
                        current_result = dict(
                            run_id=current, **{key: payload[key] for key in scope}
                        )
        children = {}
        for batch_id, status, count in child_counts:
            children.setdefault(batch_id, {})[status] = count
        items = []
        for row in rows:
            payload = row["payload"]
            started = payload.get("started_at")
            try:
                moment = datetime.fromisoformat(started)
                if moment.tzinfo is None:
                    raise ValueError("Unknown timezone")
                age = (at - moment).total_seconds()
                reason = (
                    "clock_skew"
                    if age < 0
                    else (
                        "age_threshold_exceeded"
                        if age >= older_than_minutes * 60
                        else "within_threshold"
                    )
                )
            except (ValueError, TypeError):
                age, reason = None, "start_time_unavailable"
            if row["status"] not in {"running", "validated"}:
                reason = "finished"
            items.append(
                {
                    "run_id": row["run_id"],
                    "status": row["status"],
                    "kind": payload.get("kind", "partition"),
                    "plant_id": payload.get("plant_id"),
                    "partition_id": payload.get("partition_id"),
                    "calculation_version": payload.get("calculation_version"),
                    "started_at": started,
                    "age_seconds": age,
                    "reason": reason,
                    "needs_review": reason not in {"within_threshold", "finished"},
                    "active_partition_count": published.get(row["run_id"], 0),
                    "active_child_partition_count": active_children.get(row["run_id"], 0),
                    "child_status_counts": children.get(row["run_id"], {}),
                }
            )
        if run_id:
            return {
                "mode": "read-only",
                "org_id": settings.org,
                "inspected_at": at.isoformat(),
                "older_than_minutes": older_than_minutes,
                "item": items[0] if items else None,
                "active_result_lookup_complete": lookup_complete,
                "active_result": current_result,
            }
        return {
            "mode": "read-only",
            "org_id": settings.org,
            "inspected_at": at.isoformat(),
            "older_than_minutes": older_than_minutes,
            "total_unfinished": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
            "items": items,
            "note": "Review candidates only. Verify process/Pod liveness and active pointers before retrying; no status is changed.",
        }
    finally:
        engine.dispose()
