from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

# Every stored metric written by this code base (v1 and v2) carries these fields.
# A row without them is outside the contract: readers stop instead of guessing.
REQUIRED_METRIC_FIELDS = frozenset(
    {
        "local_date",
        "estimated_energy_kwh",
        "expected_slots",
        "observed_slots",
        "valid_slots",
        "missing_slots",
        "invalid_slots",
        "source_interpolation_ratio",
        "interpolation_unknown_slots",
        "review_candidate_count",
    }
)


def require_metric_fields(metric):
    if not REQUIRED_METRIC_FIELDS <= metric.keys():
        raise ValueError("METRIC_CONTRACT_MISMATCH")
    return metric


SLOT = timedelta(minutes=15)


def day_window(day, timezone):
    zone = ZoneInfo(timezone)
    first = datetime.fromisoformat(day).replace(tzinfo=zone)
    return first.astimezone(UTC), (first + timedelta(days=1)).astimezone(UTC)


def analyze(
    inverters,
    stations,
    capacity,
    expected_ranges,
    day,
    timezone,
    poa_threshold=400,
    power_ratio=0.10,
    consecutive=3,
):
    first, end = day_window(day, timezone)
    expected = set()
    for inv, (left, right) in expected_ranges.items():
        t = max(first, left)
        while t < min(end, right + SLOT):
            expected.add((t.isoformat(), inv))
            t += SLOT
    expected_by_time = {}
    for ts, inv in expected:
        expected_by_time.setdefault(ts, set()).add(inv)
    actual = {(r["ts_utc"], r["inverter_id"]) for r in inverters}
    valid = [r for r in inverters if r["valid"]]
    missing = expected - actual
    interpolated = sum(r["interpolated"] is True for r in inverters)
    metric = {
        "local_date": day,
        "report_timezone": timezone,
        "estimated_energy_kwh": round(sum(r["value"] for r in valid) / 1000 * 0.25, 8),
        "expected_slots": len(expected),
        "observed_slots": len(actual),
        "valid_slots": len(valid),
        "missing_slots": len(missing),
        "invalid_slots": len(actual) - len(valid),
        "coverage_ratio": len(actual & expected) / len(expected) if expected else None,
        "valid_coverage_ratio": len(valid) / len(expected) if expected else None,
        "source_interpolation_ratio": interpolated / len(actual) if actual else None,
        "interpolation_unknown_slots": sum(r["interpolated"] is None for r in inverters),
        "energy_basis": "15-minute interval-average approximation; observed valid slots only",
    }
    issues = []
    if missing:
        issues.append(
            {
                "rule_id": "DQ-MISSING",
                "count": len(missing),
                "origin": "observed_grid",
                "reason": "Missing within each inverter's source observation bounds",
                "examples": sorted(missing)[:10],
            }
        )
    if interpolated:
        issues.append(
            {
                "rule_id": "DQ-INTERPOLATED",
                "count": interpolated,
                "origin": "source",
                "reason": "Source-provided interpolation, not a fault label",
            }
        )
    if metric["invalid_slots"]:
        issues.append(
            {
                "rule_id": "DQ-INVALID",
                "count": metric["invalid_slots"],
                "origin": "source",
                "reason": "Null, negative, or non-finite power excluded from energy estimate",
            }
        )
    station_by_time = {r["ts_utc"]: r for r in stations}
    by_time = {}
    for row in inverters:
        by_time.setdefault(row["ts_utc"], []).append(row)
    events, chain, series = [], [], []

    def flush():
        if len(chain) >= consecutive:
            events.append(
                {
                    "rule_id": "PERF-LOW-OUTPUT",
                    "review_status": "needs_review",
                    "confidence": "unvalidated_heuristic",
                    "start_utc": chain[0],
                    "end_utc": (datetime.fromisoformat(chain[-1]) + SLOT).isoformat(),
                    "intervals": len(chain),
                    "thresholds": {
                        "poa_wm2": poa_threshold,
                        "power_ratio": power_ratio,
                        "consecutive": consecutive,
                    },
                }
            )
        chain.clear()

    insufficient = 0
    for ts in sorted({t for t, _ in expected} | set(by_time)):
        rs = by_time.get(ts, [])
        station = station_by_time.get(ts)
        required = expected_by_time.get(ts, set())
        reliable = (
            bool(rs)
            and {r["inverter_id"] for r in rs} == required
            and all(
                r["valid"]
                and r["interpolated"] is False
                and r["document_count"] is not None
                and r["document_count"] > 0
                for r in rs
            )
        )
        reliable = (
            reliable
            and station is not None
            and station["valid"]
            and station["interpolated"] is False
            and station["document_count"] is not None
            and station["document_count"] > 0
        )
        valid_power = [r["value"] for r in rs if r["valid"]]
        # A real zero is an observation; no valid observation must remain unknown.
        power = sum(valid_power) / 1000 if valid_power else None
        poa = station["value"] if station and station["valid"] else None
        status = "INSUFFICIENT_DATA" if not reliable else "normal"
        if not reliable:
            insufficient += 1
        low = reliable and poa >= poa_threshold and power / capacity < power_ratio
        if low:
            if chain and datetime.fromisoformat(ts) - datetime.fromisoformat(chain[-1]) != SLOT:
                flush()
            chain.append(ts)
            status = "review_candidate"
        else:
            flush()
        series.append({"ts_utc": ts, "power_kw": power, "poa_wm2": poa, "assessment": status})
    flush()
    metric["insufficient_assessment_slots"] = insufficient
    metric["review_candidate_count"] = len(events)
    metric["warning_count"] = len(issues)
    return metric, issues, events, series
