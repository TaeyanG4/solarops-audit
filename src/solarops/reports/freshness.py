"""Read-only comparison of a published report with current publication evidence."""

from zoneinfo import ZoneInfo

from sqlalchemy import select

from solarops.config import CALCULATION_VERSION
from solarops.contracts.dates import month_bounds
from solarops.pipeline import canonical_hash
from solarops.reports.identity import display_scope, selection_key
from solarops.storage.postgres import active, now


def compare_report(catalog, report):
    result = {"status": "unavailable", "reason": "scope_not_recorded", "checked_at": now()}
    selection = report.get("selection")
    # Observed source kinds do not prove which filter was requested at generation time.
    if not isinstance(selection, dict) or set(selection) != {"plant_id", "source_kind"}:
        return result
    try:
        plant, kind = selection["plant_id"], selection["source_kind"]
        selection_key(selection)
        if report["org_id"] != catalog.settings.org:
            raise ValueError("Report organization mismatch")
        if report["scope"] != display_scope(plant, kind):
            raise ValueError("Report selection mismatch")
        ZoneInfo(report["timezone"])
        start, end = month_bounds(report["period"])
        original = report["partitions"]
        if not original or canonical_hash(original) != report["source_manifest_hash"]:
            raise ValueError("Invalid report evidence")
        if not report["calculation_version"]:
            raise ValueError("Missing calculation version")
    except (KeyError, TypeError, ValueError):
        return {**result, "reason": "invalid_evidence"}
    result.update(
        report_partition_count=len(original),
        report_calculation_version=report["calculation_version"],
        current_calculation_version=CALCULATION_VERSION,
    )
    if report["calculation_version"] != CALCULATION_VERSION:
        return {**result, "status": "changed", "reason": "calculation_version_changed"}
    statement = select(active.c.payload).where(
        active.c.org_id == catalog.settings.org,
        active.c.report_timezone == report["timezone"],
        active.c.calculation_version == report["calculation_version"],
        active.c.partition_id >= start,
        active.c.partition_id < end,
    )
    if plant:
        statement = statement.where(active.c.plant_id == plant)
    with catalog.engine.connect() as conn:
        current = list(
            conn.execute(statement.order_by(active.c.plant_id, active.c.partition_id)).scalars()
        )
    if kind:
        current = [
            item
            for item in current
            if item.get("source_objects")
            and all(source.get("source_kind") == kind for source in item["source_objects"])
        ]
    equal = canonical_hash(current) == report["source_manifest_hash"]
    return {
        **result,
        "status": "unchanged" if equal else "changed",
        "reason": "same_publication" if equal else "publication_changed",
        "current_partition_count": len(current),
    }
