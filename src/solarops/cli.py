import argparse
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

from solarops.config import Settings
from solarops.runtime import release_info


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
        "release": release_info(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="solarops", description="Historical PV data audits. --to is exclusive."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    admin = sub.add_parser("admin", help="Loopback-only host service manager on port 8504")
    admin.add_argument("--project-root", type=Path, default=Path.cwd())
    sub.add_parser("db-migrate")
    ons = sub.add_parser(
        "ons-sync", help="Collect ONS current/previous month; source-native MWmed only"
    )
    ons.add_argument("--period", help="Explicit YYYY-MM correction/backfill from 2022")
    ons.add_argument(
        "--as-of", help="YYYY-MM-DD schedule reference; checks previous and current month"
    )
    ons_status = sub.add_parser("ons-status", help="Read-only ONS collection status")
    ons_status.add_argument("--period", required=True)
    inspect = sub.add_parser("inspect-runs", help="Read-only review of unfinished runs")
    inspect.add_argument("--older-than-minutes", type=int, default=60)
    inspect.add_argument("--limit", type=int, default=100)
    inspect.add_argument("--offset", type=int, default=0)
    inspect.add_argument(
        "--run-id", help="Inspect one run, its active result and related Airflow attempts"
    )
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
        p.add_argument(
            "--restore",
            action="store_true",
            help="Explicitly restore a previously superseded source version; concurrency checks still apply",
        )
        if command == "backfill":
            p.add_argument("--execute", action="store_true", help="Default is a dry-run plan")
    demo = sub.add_parser("demo")
    demo.add_argument("--from", dest="start", default="2024-04-01")
    demo.add_argument("--to", dest="end", default="2024-04-08")
    demo.add_argument("--source-version", default="synthetic-v1")
    demo.add_argument("--dry-run", choices=["true", "false"], default="false")
    p = sub.add_parser(
        "replay", help="Bounded public/synthetic historical replay; dry-run by default"
    )
    p.add_argument("--source-kind", choices=["public", "synthetic"], required=True)
    p.add_argument("--plant", required=True)
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--to", dest="end", required=True)
    p.add_argument("--source-version", required=True)
    p.add_argument("--dry-run", choices=["true", "false"], default="true")
    p = sub.add_parser("analyze")
    p.add_argument("--plant")
    p.add_argument("--from", dest="start")
    p.add_argument("--to", dest="end")
    p.add_argument("--source-kind", choices=["public", "synthetic"])
    p.add_argument("--period", help="Analyze the report month instead of --from/--to")
    p = sub.add_parser("report")
    p.add_argument("--period", required=True)
    p.add_argument("--plant")
    p.add_argument("--source-kind", choices=["public", "synthetic"])
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=8501)
    p.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1")
    args = parser.parse_args(argv)
    try:
        began, cpu_began = time.perf_counter(), time.process_time()
        result = execute(args)
        if os.getenv("SOLAROPS_PROFILE") == "1" and isinstance(result, dict):
            import resource

            result["profile"] = {
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - cpu_began,
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        if result is not None:
            print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as exc:
        if args.command.startswith("ons-"):
            from solarops.acquisition.ons import failure_code
        else:
            from solarops.contracts.brpvgen import failure_code
        safe_usage = {
            "Use --period or --from/--to, not both",
            "Backfill/demo requires 1–31 days",
        }
        message = (
            str(exc)
            if isinstance(exc, ValueError) and str(exc) in safe_usage
            else ("Operation failed; see docs/runbooks/recovery.md for this code")
        )
        # Log type/code, never connection URLs, tokens or raw customer values.
        print(
            json.dumps(
                {
                    "status": "error",
                    "code": type(exc).__name__,
                    "error_code": failure_code(exc),
                    "message": message,
                }
            ),
            file=sys.stderr,
        )
        return 1


def execute(args):
    if args.command == "admin":
        import uvicorn

        from solarops.admin.app import create_admin_app

        uvicorn.run(
            create_admin_app(args.project_root),
            host="127.0.0.1",
            port=8504,
            proxy_headers=False,
            access_log=False,
        )
        return None

    from solarops.acquisition.brpvgen import checksum, fetch, inspect_source, safe_extract
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
    if args.command == "ons-sync":
        from solarops.acquisition.ons import sync

        return sync(settings, args.period, args.as_of)
    if args.command == "ons-status":
        from solarops.acquisition.ons import status

        catalog = Catalog(settings, read_only=True)
        try:
            return status(catalog, args.period)
        finally:
            catalog.engine.dispose()
    if args.command == "inspect-runs":
        from solarops.diagnostics import inspect_runs

        return inspect_runs(
            settings, args.older_than_minutes, args.limit, args.offset, run_id=args.run_id
        )
    if args.command == "replay":
        from solarops.replay import replay

        return replay(
            settings,
            args.source_kind,
            args.plant,
            args.start,
            args.end,
            args.source_version,
            args.dry_run == "true",
        )
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
        from solarops.replay import run_demo

        return run_demo(settings, args.start, args.end, args.source_version)
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
            restore=args.restore,
        )
    if args.command == "analyze":
        if args.period:
            from solarops.reports.render import month_bounds

            if args.start or args.end:
                raise ValueError("Use --period or --from/--to, not both")
            args.start, args.end = month_bounds(args.period)
        catalog = Catalog(settings, read_only=True)
        try:
            result = catalog.snapshot(
                settings.org, args.start, args.end, args.plant, args.source_kind
            )
        finally:
            catalog.engine.dispose()
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
