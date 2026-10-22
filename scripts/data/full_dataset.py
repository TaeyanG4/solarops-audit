"""Explicit full public-data audit. Never imported by tests or installation."""

import argparse
import json
import os
import platform
import time
from pathlib import Path

import psutil

from solarops.config import Settings
from solarops.pipeline import ingest
from solarops.reports.render import build_report

parser = argparse.ArgumentParser()
parser.add_argument("--services", action="store_true")
args = parser.parse_args()
if args.services:
    values = dict(
        line.split("=", 1)
        for line in Path(".env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    os.environ.update(
        SOLAROPS_DATA_DIR="data/service-full",
        SOLAROPS_DATABASE_URL=f"postgresql+psycopg://solarops:{values['APP_DB_PASSWORD']}@127.0.0.1:55432/solarops",
        SOLAROPS_S3_ENDPOINT="http://127.0.0.1:59000",
        SOLAROPS_S3_ACCESS_KEY=values["MINIO_ROOT_USER"],
        SOLAROPS_S3_SECRET_KEY=values["MINIO_ROOT_PASSWORD"],
    )
settings = Settings()
source = Path("data/source")
out = Path(
    "artifacts/full-dataset-services.jsonl" if args.services else "artifacts/full-dataset.jsonl"
)
out.parent.mkdir(exist_ok=True)
start = time.perf_counter()
process = psutil.Process()
with out.open("a", encoding="utf-8") as log:
    log.write(
        json.dumps(
            {
                "event": "start",
                "platform": platform.platform(),
                "python": platform.python_version(),
                "logical_cpus": psutil.cpu_count(),
                "ram_bytes": psutil.virtual_memory().total,
            }
        )
        + "\n"
    )
    for inverter in sorted((source / "inverter/BR-PVGen_inverter").glob("*.csv")):
        began = time.perf_counter()
        result = ingest(
            settings,
            source / "BR-PVGen_metadata.csv",
            inverter,
            source / "station/BR-PVGen_meteorological" / inverter.name,
            inverter.stem,
            "2024-03-26",
            "2025-06-10",
            "brpvgen-v1",
            "public",
        )
        info = {
            "plant": inverter.stem,
            "rows": result["rows"],
            "partitions": result["partitions"],
            "seconds": round(time.perf_counter() - began, 3),
            "rss_bytes": process.memory_info().rss,
            "peak_rss_bytes": getattr(process.memory_info(), "peak_wset", None),
            "input_bytes": inverter.stat().st_size,
        }
        log.write(json.dumps(info) + "\n")
        log.flush()
        print(json.dumps(info), flush=True)
    report = build_report(settings, "2024-04", source_kind="public")
    build_report(settings, "2024-04", plant="PS_001", source_kind="public")
    log.write(
        json.dumps(
            {
                "event": "complete",
                "seconds": round(time.perf_counter() - start, 3),
                "report": report,
            }
        )
        + "\n"
    )
    print(
        json.dumps({"complete": True, "seconds": time.perf_counter() - start, "report": report}),
        flush=True,
    )
