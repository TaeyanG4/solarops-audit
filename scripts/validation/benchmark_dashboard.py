"""Measure the old per-plant request pattern against the bounded overview API."""

import argparse
import json
import statistics
import time
from pathlib import Path
from urllib.request import urlopen

from solarops.reports.render import month_bounds

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8502")
parser.add_argument("--mode", choices=["legacy", "overview"], required=True)
parser.add_argument("--period", default="2024-04")
parser.add_argument("--repeat", type=int, default=5)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
start, end = month_bounds(args.period)
measurements = []
for _ in range(args.repeat):
    began, sizes = time.perf_counter(), []

    def get(path, sizes=sizes):
        with urlopen(args.url.rstrip("/") + path, timeout=60) as response:
            body = response.read()
        sizes.append(len(body))
        return json.loads(body)

    if args.mode == "legacy":
        plants = get("/api/v1/plants?limit=100")["items"]
        for plant in plants:
            get(f"/api/v1/plants/{plant['plant_id']}/metrics?limit=1&from={start}&to={end}")
    else:
        get(f"/api/v1/overview?period={args.period}")
    measurements.append(
        {
            "ms": round((time.perf_counter() - began) * 1000, 3),
            "requests": len(sizes),
            "response_bytes": sum(sizes),
        }
    )
result = {
    "mode": args.mode,
    "period": args.period,
    "samples": measurements,
    "median_ms": statistics.median(row["ms"] for row in measurements),
    "note": "Sequential local HTTP requests; same month, all source kinds; no cache. Different response shapes.",
}
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open("x", encoding="utf-8") as out:
    json.dump(result, out, indent=2)
print(json.dumps(result, indent=2))
