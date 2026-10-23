"""Report selection identity is independent of the legacy display scope."""

import json

from solarops.config import identifier


def selection_key(selection):
    if not isinstance(selection, dict) or set(selection) != {"plant_id", "source_kind"}:
        raise ValueError("Invalid report selection")
    plant, kind = selection["plant_id"], selection["source_kind"]
    if plant is not None:
        identifier(plant)
    if kind not in (None, "public", "synthetic"):
        raise ValueError("Unknown source kind")
    # ':' and JSON punctuation cannot occur in a legacy plant/scope identifier.
    return "selection:" + json.dumps([plant, kind], separators=(",", ":"))


def display_scope(plant, kind):
    return plant if plant is not None else ("all-" + kind if kind else "all")
