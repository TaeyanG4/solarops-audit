"""Bounded, organization-scoped read models for the audit workspace."""

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func, select

from solarops.config import CALCULATION_VERSION
from solarops.contracts.dates import month_bounds
from solarops.storage.postgres import active, metrics, runs

COUNTS = (
    "expected_slots",
    "observed_slots",
    "valid_slots",
    "missing_slots",
    "invalid_slots",
    "interpolation_unknown_slots",
    "review_candidate_count",
)


def empty_totals():
    return dict.fromkeys(
        (*COUNTS, "estimated_energy_kwh", "interpolated_slots", "partition_count"), 0
    )


def add_metric(total, metric):
    for key in COUNTS:
        total[key] += metric.get(key, 0)
    total["estimated_energy_kwh"] += metric["estimated_energy_kwh"]
    total["interpolated_slots"] += round(
        (metric["source_interpolation_ratio"] or 0) * metric["observed_slots"]
    )
    total["partition_count"] += 1


def finish(total):
    expected, observed = total["expected_slots"], total["observed_slots"]
    total["estimated_energy_kwh"] = round(total["estimated_energy_kwh"], 3)
    # Weight by slots, not by daily percentages. Unknown denominators stay unknown.
    total["coverage_ratio"] = (expected - total["missing_slots"]) / expected if expected else None
    total["valid_coverage_ratio"] = total["valid_slots"] / expected if expected else None
    total["source_interpolation_ratio"] = (
        total["interpolated_slots"] / observed if observed else None
    )
    return total


def fleet_overview(catalog, period, source_kind=None):
    start, end = month_bounds(period)
    source = active.c.payload["source_objects"][0]["source_kind"].as_string()
    stmt = (
        select(
            active.c.plant_id,
            active.c.partition_id,
            metrics.c.payload.label("metric"),
            source.label("source_kind"),
            active.c.payload["metadata"]["nominal_power_kw"].as_float().label("capacity_kw"),
            active.c.payload["metadata"]["brazil_federative_unit"].as_string().label("region"),
        )
        .join(metrics, active.c.run_id == metrics.c.run_id)
        .where(
            active.c.org_id == catalog.settings.org,
            active.c.report_timezone == catalog.settings.timezone,
            active.c.calculation_version == CALCULATION_VERSION,
            active.c.partition_id >= start,
            active.c.partition_id < end,
        )
        .order_by(active.c.plant_id, active.c.partition_id)
    )
    if source_kind:
        stmt = stmt.where(source == source_kind)
    summary, plants, days = empty_totals(), {}, {}
    with catalog.engine.connect() as conn:
        # One SELECT; no source manifests, event payloads or per-plant queries.
        for row in conn.execute(stmt).mappings():
            plant = plants.setdefault(
                row["plant_id"],
                dict(
                    empty_totals(),
                    plant_id=row["plant_id"],
                    capacity_kw=row["capacity_kw"],
                    region=row["region"],
                    source_kinds=set(),
                    first_day=row["partition_id"],
                ),
            )
            plant["last_day"] = row["partition_id"]
            plant["source_kinds"].add(row["source_kind"])
            day = days.setdefault(row["partition_id"], empty_totals())
            for total in (summary, plant, day):
                add_metric(total, row["metric"])
    expected_days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    for plant in plants.values():
        finish(plant)
        plant["source_kinds"] = sorted(plant["source_kinds"])
        plant["period_complete"] = plant["partition_count"] == expected_days
    timeline = []
    for offset in range(expected_days):
        day = (date.fromisoformat(start) + timedelta(days=offset)).isoformat()
        value = finish(days[day]) if day in days else None
        timeline.append({"day": day, "metrics": value})
    return {
        "period": period,
        "timezone": catalog.settings.timezone,
        "source_kind": source_kind or "all",
        "calculation_version": CALCULATION_VERSION,
        "summary": dict(
            finish(summary),
            plant_count=len(plants),
            complete_plants=sum(p["period_complete"] for p in plants.values()),
        ),
        "plants": sorted(
            plants.values(),
            key=lambda p: (
                p["valid_coverage_ratio"] is not None,
                p["valid_coverage_ratio"] or 0,
                p["plant_id"],
            ),
        ),
        "timeline": timeline,
    }


def available_periods(catalog, source_kind=None):
    """Months with published data, independent of energy values or report publication."""
    period = func.substr(active.c.partition_id, 1, 7)
    statement = (
        select(
            period.label("period"),
            func.count().label("partition_count"),
            func.count(func.distinct(active.c.plant_id)).label("plant_count"),
        )
        .where(
            active.c.org_id == catalog.settings.org,
            active.c.report_timezone == catalog.settings.timezone,
            active.c.calculation_version == CALCULATION_VERSION,
        )
        .group_by(period)
        .order_by(period.desc())
    )
    if source_kind:
        statement = statement.where(
            active.c.payload["source_objects"][0]["source_kind"].as_string() == source_kind
        )
    with catalog.engine.connect() as conn:
        items = [dict(row) for row in conn.execute(statement).mappings()]
    return {
        "items": items,
        "source_kind": source_kind or "all",
        "timezone": catalog.settings.timezone,
        "calculation_version": CALCULATION_VERSION,
    }


def run_history(catalog, level="all", status=None, plant=None, offset=0, limit=50):
    predicates = [runs.c.org_id == catalog.settings.org]
    kind = runs.c.payload["kind"].as_string()
    if level == "batch":
        predicates.append(kind == "ingest")
    elif level == "partition":
        # Legacy day runs predate the explicit kind field.
        predicates.append(func.coalesce(kind, "partition") != "ingest")
    if plant:
        predicates.append(runs.c.payload["plant_id"].as_string() == plant)
    updated = func.coalesce(
        runs.c.payload["finished_at"].as_string(), runs.c.payload["started_at"].as_string(), ""
    )
    with catalog.engine.connect() as conn:
        counts = Counter(
            dict(
                conn.execute(
                    select(runs.c.status, func.count()).where(*predicates).group_by(runs.c.status)
                ).all()
            )
        )
        if status:
            predicates.append(runs.c.status == status)
        data = conn.execute(
            select(runs, updated.label("updated_at"))
            .where(*predicates)
            .order_by(updated.desc(), runs.c.run_id.desc())
            .offset(offset)
            .limit(limit)
        ).mappings()
        items = [
            dict(r["payload"], run_id=r["run_id"], status=r["status"], updated_at=r["updated_at"])
            for r in data
        ]
    return {
        "items": items,
        "total": counts[status] if status else counts.total(),
        "status_counts": dict(counts),
        "level": level,
        "offset": offset,
        "limit": limit,
    }
