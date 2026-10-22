import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

from solarops.config import Settings


def doctor():
    tools = {
        t: shutil.which(t) for t in ("python", "uv", "docker", "make", "helm", "kubectl", "kind")
    }
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "tools": tools,
        "free_disk_gb": round(shutil.disk_usage(Path.cwd()).free / 1024**3, 2),
        "native_demo_ready": sys.version_info[:2] == (3, 12),
        "note": "Docker/kind/Helm are needed for infrastructure validation, not offline tests",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="solarops", description="Historical PV data audits. --to is exclusive."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("db-migrate")
    source = sub.add_parser("source").add_subparsers(dest="source_command", required=True)
    source.add_parser("inspect")
    fetch = source.add_parser("fetch")
    fetch.add_argument("--files", nargs="+", default=["Readme.txt", "BR-PVGen_metadata.csv"])
    fetch.add_argument("--allow-large", action="store_true")
    fetch.add_argument("--destination", type=Path, default=Path("data/source"))
    check = source.add_parser("checksum")
    check.add_argument("path", type=Path)
    extract = source.add_parser("extract")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)
    for command in ("ingest", "backfill"):
        p = sub.add_parser(command)
        for field in ("metadata", "inverter", "station"):
            p.add_argument("--" + field, type=Path, required=True)
        p.add_argument("--plant", required=True)
        p.add_argument("--from", dest="start", required=True)
        p.add_argument("--to", dest="end", required=True)
        p.add_argument("--source-version", required=True)
        p.add_argument("--source-kind", choices=["synthetic", "public"], default="synthetic")
        p.add_argument("--fail-at", choices=["before_commit", "during_commit"])
        if command == "backfill":
            p.add_argument("--execute", action="store_true", help="Default is a dry-run plan")
    demo = sub.add_parser("demo")
    demo.add_argument("--from", dest="start", default="2024-04-01")
    demo.add_argument("--to", dest="end", default="2024-04-08")
    demo.add_argument("--source-version", default="synthetic-v1")
    demo.add_argument("--dry-run", choices=["true", "false"], default="false")
    p = sub.add_parser("analyze")
    p.add_argument("--plant")
    p.add_argument("--from", dest="start")
    p.add_argument("--to", dest="end")
    p = sub.add_parser("report")
    p.add_argument("--period", required=True)
    p.add_argument("--plant")
    p.add_argument("--source-kind", choices=["public", "synthetic"])
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=8501)
    p.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")
    args = parser.parse_args(argv)
    try:
        result = execute(args)
        if result is not None:
            print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as exc:
        # Log type/code, never connection URLs, tokens or raw customer values.
        print(
            json.dumps(
                {
                    "status": "error",
                    "code": type(exc).__name__,
                    "message": str(exc)
                    if isinstance(exc, ValueError | RuntimeError)
                    else "Operation failed; inspect local service logs",
                }
            ),
            file=sys.stderr,
        )
        return 1


def execute(args):
    from solarops.acquisition.brpvgen import checksum, fetch, inspect_source, safe_extract
    from solarops.fixtures import generate
    from solarops.pipeline import ingest
    from solarops.reports.render import build_report
    from solarops.storage.postgres import Catalog

    if args.command == "doctor":
        return doctor()
    if args.command == "source":
        match args.source_command:
            case "inspect":
                return inspect_source()
            case "fetch":
                return fetch(args.destination, args.files, args.allow_large)
            case "checksum":
                return {"sha256": checksum(args.path), "byte_size": args.path.stat().st_size}
            case "extract":
                return safe_extract(args.archive, args.destination)
    settings = Settings()
    if args.command == "db-migrate":
        Catalog(settings)
        return {"status": "ready", "schema_version": "1"}
    if args.command in ("demo", "backfill"):
        from datetime import date

        days = (date.fromisoformat(args.end) - date.fromisoformat(args.start)).days
        if not 1 <= days <= 31:
            raise ValueError("Backfill/demo requires 1–31 days")
        dry = args.dry_run == "true" if args.command == "demo" else not args.execute
        if dry:
            return {
                "dry_run": True,
                "from": args.start,
                "to_exclusive": args.end,
                "days": days,
                "source_version": args.source_version,
            }
    if args.command == "demo":
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
            args.start,
            args.end,
            args.source_version,
            fail_at=fail_at,
        )
        result["report"] = build_report(settings, args.start[:7], "DEMO_01")
        return result
    if args.command in ("ingest", "backfill"):
        return ingest(
            settings,
            args.metadata,
            args.inverter,
            args.station,
            args.plant,
            args.start,
            args.end,
            args.source_version,
            args.source_kind,
            args.fail_at,
        )
    if args.command == "analyze":
        result = Catalog(settings).snapshot(settings.org, args.start, args.end, args.plant)
        if not result:
            raise ValueError("NO_ACTIVE_PARTITIONS")
        return {
            "partitions": len(result),
            "metrics": [r["metric"] for r in result],
            "logical_hashes": [r["payload"]["logical_content_hash"] for r in result],
        }
    if args.command == "report":
        return build_report(settings, args.period, args.plant, args.source_kind)
    if args.command == "serve":
        import uvicorn

        from solarops.api.app import create_app

        uvicorn.run(create_app(settings), host=args.host, port=args.port)


if __name__ == "__main__":
    sys.exit(main())
