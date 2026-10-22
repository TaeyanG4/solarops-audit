"""Grouped navigation/admin checks. --lifecycle explicitly stops/restarts local SolarOps.

Requires the provisioned demo on 8502 and host manager on 8504. No datasets fetched.
Lifecycle check restores initially running kind; Airflow Compose stays initially stopped.
"""

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path


def read(url):
    with urllib.request.urlopen(url, timeout=25) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lifecycle", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary = os.environ.get("AGENT_BROWSER_BIN") or shutil.which("agent-browser")
    if binary and Path(binary).suffix.lower() in {".cmd", ".ps1"}:
        binary = str(
            Path(binary).parent / "node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
        )
    session = "solarops-workspace-" + uuid.uuid4().hex[:8]
    log = []
    base = "http://127.0.0.1:8502/"
    admin = "http://127.0.0.1:8504/"

    def run(*command):
        out = args.output / "command.json"
        with (
            out.open("w", encoding="utf-8") as stdout,
            (args.output / "stderr.txt").open("w", encoding="utf-8") as stderr,
        ):
            result = subprocess.run(
                [binary, "--session", session, "--json", *command],
                stdout=stdout,
                stderr=stderr,
                timeout=55,
            )
        data = json.loads(out.read_text(encoding="utf-8"))
        log.append({"command": command, "result": data})
        (args.output / "checks.json").write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        assert result.returncode == 0 and data.get("success"), data
        return data["data"]

    def check(js):
        assert run("eval", js)["result"] is True, js

    def wait_operation():
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            result = read(admin + "api/admin/status")
            op = result["operation"]
            if op and op["state"] != "running":
                assert op["state"] == "succeeded", op
                return result
            time.sleep(2)
        raise AssertionError("Lifecycle timeout; inspect real state before retry")

    initial = read(admin + "api/admin/status")
    (args.output / "status-before.json").write_text(
        json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    original = read(base + "api/v1/overview?period=2024-04&source_kind=public")
    lifecycle = []

    def operate(target, action):
        run("click", f'[data-action="{target}-{action}"]')
        run("wait", "dialog[open]")
        check('document.activeElement.id === "cancel-action"')
        run("click", "#confirm-action")
        result = wait_operation()
        lifecycle.append(result)
        (args.output / "lifecycle.json").write_text(
            json.dumps(lifecycle, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        run("click", "#admin-refresh")
        run("wait", "--fn", '!document.querySelector("[data-action=workspace-start]").disabled')
        return result

    try:
        run("open", base + "?view=overview&period=2024-04&source=public")
        run("wait", ".energy-chart")
        run("snapshot", "-i")
        check(
            'document.querySelectorAll(".nav-group").length === 3 && document.querySelectorAll("nav a").length === 7'
        )
        for page, wait in [
            ("plants", ".plant-table"),
            ("quality", ".quality-table"),
            ("sources", ".lineage-steps"),
            ("system", ".system-view"),
            ("reports", ".report-sheet"),
        ]:
            run("open", base + f"?view={page}&period=2024-04&source=public")
            run("wait", wait)
            check(
                f'document.querySelector("[data-view={page}]").getAttribute("aria-current") === "page"'
            )
            for width in (1440, 768, 390):
                run("set", "viewport", str(width), "1000", "2")
                check("document.documentElement.scrollWidth === innerWidth")
                check(
                    'Array.from(document.querySelectorAll("p,td,th,label,button,nav a")).filter(e => e.checkVisibility() && e.textContent.trim()).every(e => parseFloat(getComputedStyle(e).fontSize) >= 14)'
                )
                audit = run("a11y")
                assert audit["counts"]["violations"] == 0, audit
                run("screenshot", str(args.output / f"{page}-{width}.png"), "--full")
                run("screenshot", str(args.output / f"{page}-viewport-{width}.png"))
        run("set", "viewport", "390", "1000", "2")
        run("click", ".nav-toggle")
        check('document.querySelector(".nav-toggle").getAttribute("aria-expanded") === "true"')
        run("screenshot", str(args.output / "mobile-navigation.png"))
        run("focus", "[data-view=quality]")
        run("press", "Escape")
        check(
            'document.activeElement.classList.contains("nav-toggle") && document.querySelector(".nav-toggle").getAttribute("aria-expanded") === "false"'
        )
        run("click", ".nav-toggle")
        run("click", "[data-view=quality]")
        run("wait", ".quality-table")
        check(
            'location.search.includes("source=public") && location.search.includes("period=2024-04")'
        )
        # Exercise the authored controls with real keyboard/click input, not value injection.
        run("click", "[data-select-for=source]")
        check('document.querySelector(".select-options:popover-open") !== null')
        run("screenshot", str(args.output / "source-options-mobile.png"))
        assert run("a11y")["counts"]["violations"] == 0
        run("press", "End")
        run("press", "Enter")
        run("wait", ".quality-table")
        check('location.search.includes("source=synthetic")')
        run("click", "[data-select-for=source]")
        run("press", "Home")
        run("press", "ArrowDown")
        run("press", "Enter")
        run("wait", ".quality-table")
        check('location.search.includes("source=public")')
        run("click", "#period-open")
        run("wait", ".month-dialog[open]")
        run("screenshot", str(args.output / "month-picker-mobile.png"))
        assert run("a11y")["counts"]["violations"] == 0
        run("press", "Escape")
        check('document.activeElement.id === "period-open"')
        run("click", "#period-open")
        run("fill", ".month-year input", "1990")
        run("click", ".month-option:nth-child(1)")
        run("wait", ".empty")
        check('location.search.includes("period=1990-01")')
        run("open", base + "?view=reports&period=2024-04&source=public&plant=PS_001")
        run("wait", ".report-sheet")
        check(
            '!document.querySelector("iframe") && document.querySelector(".report-energy").textContent.includes("585,980.28")'
        )
        run("click", ".report-daily-details summary")
        check('document.querySelectorAll(".report-daily tbody tr").length === 30')
        run("screenshot", str(args.output / "report-daily-mobile.png"))
        run("click", ".report-sources summary")
        check('document.querySelector(".report-sources[open]") !== null')
        run("click", 'a[target="_blank"][href$="report.html"]')
        # Explicit open avoids depending on which tab a target=_blank action selects.
        report_id = next(
            r["report_id"]
            for r in read(base + "api/v1/reports?period=2024-04&source_kind=public")["items"]
            if r["scope"] == "PS_001"
        )
        run("open", base + f"reports/{report_id}/report.html")
        run("wait", ".report-export")
        for width in (1440, 768, 390):
            run("set", "viewport", str(width), "1000", "2")
            check("document.documentElement.scrollWidth === innerWidth")
            assert run("a11y")["counts"]["violations"] == 0
            run("screenshot", str(args.output / f"print-report-{width}.png"))
        run("open", admin)
        run("wait", ".service-row")
        run("snapshot", "-i")
        run("click", '[data-action="database-stop"]')
        run("wait", "dialog[open]")
        check(
            'document.querySelector("#action-impact").textContent.includes("Kubernetes 환경은 유지")'
        )
        run("screenshot", str(args.output / "confirm-mobile.png"))
        run("press", "Escape")
        check('!document.querySelector("dialog").open')
        assert read(admin + "api/admin/status")["operation"] == initial["operation"]
        if args.lifecycle:
            # An explicit destructive-free lifecycle check; changes live availability.
            assert all(
                i["state"] != "running"
                for i in initial["containers"]
                if i["service"].startswith("airflow") or i["service"] == "worker"
            ), "Stop active processing before running lifecycle validation"
            stopped = operate("workspace", "stop")
            assert all(
                i["state"] not in {"running", "restarting", "paused"} for i in stopped["containers"]
            )
            assert not stopped["dashboard_ready"]
            started = operate("workspace", "start")
            assert started["dashboard_ready"] and started["storage_ready"]
            if any(
                i["service"] == "kind" and i["state"] == "running" for i in initial["containers"]
            ):
                operate("kubernetes", "start")
            assert read(base + "api/v1/overview?period=2024-04&source_kind=public") == original
        for width in (1440, 768, 390):
            run("set", "viewport", str(width), "1000", "2")
            run("eval", "scrollTo(0,0)")
            check("document.documentElement.scrollWidth === innerWidth")
            audit = run("a11y")
            assert audit["counts"]["violations"] == 0, audit
            run("screenshot", str(args.output / f"admin-{width}.png"), "--full")
            run("screenshot", str(args.output / f"admin-viewport-{width}.png"))
        run("set", "viewport", "320", "900")
        check("document.documentElement.scrollWidth === innerWidth")
        assert not run("errors").get("errors"), "Browser errors"
        result = {
            "status": "pass",
            "commands": len(log),
            "axe_audits": 23,
            "lifecycle_executed": args.lifecycle,
            "api_unchanged": read(base + "api/v1/overview?period=2024-04&source_kind=public")
            == original,
        }
        (args.output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
    finally:
        run("close")


if __name__ == "__main__":
    main()
