"""Bounded historical replay shared by local and Kubernetes Airflow tasks."""

import os
import re
import time
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from solarops.config import identifier
from solarops.contracts.brpvgen import read_metadata
from solarops.pipeline import ingest, source_bounds


def plan_replay(settings, source_kind, plant, start, end, source_version):
    identifier(plant)
    identifier(source_version)
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    if not 1 <= days <= 31:
        raise ValueError("Replay requires 1–31 days; --to is exclusive")
    plan = {
        "dry_run": True,
        "source_kind": source_kind,
        "plant_id": plant,
        "from": start,
        "to_exclusive": end,
        "days": days,
        "source_version": source_version,
        "report_timezone": settings.timezone,
    }
    if source_kind == "synthetic":
        if plant != "DEMO_01":
            raise ValueError("Synthetic replay requires plant DEMO_01")
        if start < "2024-04-01" or end > "2024-04-08":
            raise ValueError("Synthetic fixture covers 2024-04-01 through 2024-04-07")
        return plan
    if source_kind != "public":
        raise ValueError("Replay supports only public or synthetic sources")
    if settings.org != "demo":
        raise ValueError("Public BR-PVGen belongs to demo org")
    if not re.fullmatch(r"PS_[0-9]{3}", plant):
        raise ValueError("Public replay requires a BR-PVGen plant such as PS_001")
    root = settings.source_root.resolve()
    paths = {
        "metadata": root / "BR-PVGen_metadata.csv",
        "inverter": root / "inverter" / "BR-PVGen_inverter" / f"{plant}.csv",
        "station": root / "station" / "BR-PVGen_meteorological" / f"{plant}.csv",
    }
    for kind, path in paths.items():
        if not path.resolve().is_relative_to(root):
            raise ValueError("SOURCE_PATH_OUTSIDE_ROOT")
        if not path.is_file():
            raise ValueError(f"MISSING_PUBLIC_SOURCE: {kind}; prepare SOLAROPS_SOURCE_DIR first")
    metadata = read_metadata(paths["metadata"])
    if plant not in metadata:
        raise ValueError("UNKNOWN_PLANT")
    # A scheduled replay must not silently succeed when its whole window has no data.
    zone = ZoneInfo(settings.timezone)
    bounds = source_bounds(paths["inverter"], plant, metadata)
    if not any(
        left.astimezone(zone).date() < date.fromisoformat(end)
        and right.astimezone(zone).date() >= date.fromisoformat(start)
        for left, right in bounds.values()
    ):
        raise ValueError("NO_SOURCE_DATA_IN_WINDOW")
    plan["inputs"] = {kind: str(path) for kind, path in paths.items()}
    return plan


def replay(settings, source_kind, plant, start, end, source_version, dry_run=True):
    plan = plan_replay(settings, source_kind, plant, start, end, source_version)
    if dry_run:
        return plan
    if source_kind == "synthetic":
        return run_demo(settings, start, end, source_version)
    paths = {kind: Path(path) for kind, path in plan["inputs"].items()}
    return ingest(
        settings,
        paths["metadata"],
        paths["inverter"],
        paths["station"],
        plant,
        start,
        end,
        source_version,
        source_kind="public",
    )


def run_demo(settings, start, end, source_version):
    from solarops.fixtures import generate
    from solarops.reports.render import build_report

    paths = generate(settings.root / "fixtures" / "synthetic-v1")
    delay = int(os.getenv("SOLAROPS_TEST_DELAY", "0"))
    if delay:
        time.sleep(min(delay, 120))
    fail_at = None
    marker = os.getenv("SOLAROPS_FAIL_ONCE_MARKER")
    if marker:
        path = settings.root / "fault-markers" / Path(marker).name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("injected", encoding="utf-8")
            fail_at = "during_commit"
    result = ingest(
        settings,
        paths["metadata"],
        paths["inverter"],
        paths["station"],
        "DEMO_01",
        start,
        end,
        source_version,
        fail_at=fail_at,
    )
    result["report"] = build_report(settings, start[:7], "DEMO_01", "synthetic")
    return result
