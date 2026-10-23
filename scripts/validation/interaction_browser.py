"""Read-only browser regression for scroll selectors, admin tabs and series gaps.

Requires prepared localhost 8502/8504 services. Fixtures affect only this browser;
never starts/stops containers, submits admin actions or downloads source datasets.
"""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request
import uuid
from pathlib import Path


def read(url):
    with urllib.request.urlopen(url, timeout=25) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selectors-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary = os.environ.get("AGENT_BROWSER_BIN") or shutil.which("agent-browser")
    if binary and Path(binary).suffix.lower() in {".cmd", ".ps1"}:
        binary = str(
            Path(binary).parent / "node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
        )
    session = "solarops-interactions-" + uuid.uuid4().hex[:8]
    base, admin = "http://127.0.0.1:8502/", "http://127.0.0.1:8504/"
    logs, audits = [], []

    def run(*command):
        output = args.output / "command.json"
        # A newly spawned browser daemon inherits output handles on Windows.
        # Files avoid waiting for that long-lived daemon to close a pipe.
        with (
            output.open("w", encoding="utf-8") as stdout,
            (args.output / "stderr.txt").open("w", encoding="utf-8") as stderr,
        ):
            result = subprocess.run(
                [binary, "--session", session, "--json", *command],
                stdout=stdout,
                stderr=stderr,
                timeout=55,
            )
        data = json.loads(output.read_text(encoding="utf-8"))
        logs.append({"command": command, "result": data})
        (args.output / "checks.json").write_text(
            json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        assert result.returncode == 0 and data.get("success"), data
        return data["data"]

    def check(js):
        assert run("eval", js)["result"] is True, js

    def screenshot(name):
        run("screenshot", str(args.output / (name + ".png")))

    def audit():
        result = run("a11y")
        audits.append(result["counts"])
        assert result["counts"]["violations"] == 0, result

    def complete():
        errors = run("errors")
        assert not errors.get("errors"), errors
        assert read(base + series_path) == before
        assert read(base + "api/v1/overview?period=2024-04&source_kind=public") == overview
        assert read(admin + "api/admin/status")["operation"] == operation
        (args.output / "summary.json").write_text(
            json.dumps(
                {
                    "scope": "selectors" if args.selectors_only else "interactions",
                    "commands": len(logs),
                    "a11y_audits": len(audits),
                    "violations": 0,
                    "viewports": [1440, 768, 390],
                    "api_unchanged": True,
                    "admin_no_action_submitted": True,
                    "browser_fixture_only": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print((args.output / "summary.json").read_text())

    series_path = "api/v1/plants/PS_001/series?day=2024-04-30"
    series_url = base + "?view=series&period=2024-04&source=public&plant=PS_001&day=2024-04-30"
    before = read(base + series_path)
    overview = read(base + "api/v1/overview?period=2024-04&source_kind=public")
    operation = read(admin + "api/admin/status")["operation"]
    try:
        run("open", base + "?view=overview&period=2024-04&source=public")
        for width in (1440, 768, 390):
            run("set", "viewport", str(width), "1000", "2")
            for page, label in (("runs", "실행 단위"), ("reports", "보고서 선택")):
                run("open", base + f"?view={page}&period=2024-04&source=public&plant=PS_001")
                selector = f'[role=combobox][aria-label="{label}"]'
                run("wait", selector)
                run("snapshot", "-i")
                run("click", selector)
                check('!!document.querySelector(":popover-open")')
                # Trigger/list initially meet, with either above or below placement.
                attached = (
                    f"(() => {{ const t=document.querySelector('{selector}');"
                    "const p=document.querySelector(':popover-open'); if (!p) return false;"
                    "const a=t.getBoundingClientRect(), b=p.getBoundingClientRect();"
                    "return t.getAttribute('aria-expanded') === 'true' && "
                    "Math.min(Math.abs(b.top-a.bottom-6),Math.abs(a.top-b.bottom-6)) < 1 && "
                    "b.left >= 11 && b.right <= innerWidth-11 && b.top >= 11 && b.bottom <= innerHeight-11; })()"
                )
                check(attached)
                screenshot(f"{page}-open-{width}")
                initial_y = run("eval", "scrollY")["result"]
                run("mouse", "move", str(width - 12), "800")
                run("mouse", "wheel", "180")
                run("wait", "--fn", f"scrollY > {initial_y + 30}")
                screenshot(f"{page}-scrolled-{width}")
                check(attached)
                audit()
                run("set", "viewport", str(width), "800", "2")
                check(attached)
                run("set", "viewport", str(width), "1000", "2")
                run("mouse", "wheel", "-90")
                run("wait", "--fn", f"scrollY < {initial_y + 160}")
                check(attached)
                run("press", "Escape")
                check(f"document.activeElement.matches('{selector}')")
                check('!document.querySelector(":popover-open")')
                run("click", selector)
                run("click", "h1")
                check('!document.querySelector(":popover-open")')
                run("click", selector)
                run("press", "Tab")
                check('!document.querySelector(":popover-open")')
                # A control entirely outside the viewport should not leave an orphan.
                run("click", selector)
                run(
                    "eval",
                    f"window.scrollBy(0, document.querySelector('{selector}').getBoundingClientRect().bottom + 20)",
                )
                run("wait", "--fn", '!document.querySelector(":popover-open")')
                check(
                    f"document.querySelector('{selector}').getAttribute('aria-expanded') === 'false'"
                )
                run("eval", "scrollTo(0,0)")
                run("click", selector)
                run("press", "Escape")
                check(f"document.activeElement.matches('{selector}')")

            # The real 30-day selector must scroll internally and retain keyboard focus.
            run("open", base + "?view=overview&period=2024-04&source=public")
            run("wait", ".chart-controls .select-trigger")
            run("click", ".chart-controls .select-trigger")
            page_y = run("eval", "scrollY")["result"]
            run("scroll", "down", "120", "--selector", ".select-options:popover-open")
            check(
                '!!document.querySelector(":popover-open") && document.querySelector(":popover-open").scrollTop > 0'
            )
            run("press", "End")
            check(f"scrollY === {page_y} && !!document.querySelector(':popover-open')")
            run("press", "Enter")
            check(
                'document.querySelector(".chart-controls select").value === "29" && !document.querySelector(":popover-open")'
            )
            run("click", ".chart-controls .select-trigger")
            run("press", "Home")
            run("press", "Enter")
            check('document.querySelector(".chart-controls select").value === "0"')

            if args.selectors_only:
                continue

            run("open", series_url)
            run("wait", ".observation-chart [data-series]")
            check("document.documentElement.scrollWidth === innerWidth")
            check(
                'document.querySelectorAll("[data-gap-series=power_kw]").length === 1 && document.querySelectorAll("[data-gap-series=poa_wm2]").length === 3'
            )
            check(
                'document.querySelector(".observation-summary").textContent.includes("전력 10 / 96") && document.querySelector(".observation-summary").textContent.includes("POA 57 / 96")'
            )
            # CSS-to-SVG scale must stay 1 so 14px labels remain 14 CSS pixels.
            check(
                'Math.abs(document.querySelector(".observation-chart text").getScreenCTM().a - 1) < .01'
            )
            run("click", ".observation-gaps summary")
            check(
                'document.querySelector(".observation-gaps").textContent.includes("17:45–20:00 (10개 시각)")'
            )
            run(
                "eval",
                'document.querySelector(".observation-chart-wrap").closest("section").scrollIntoView()',
            )
            screenshot(f"series-{width}")
            audit()

            # Legacy URL redirects directly; the sidebar also targets admin directly.
            run("open", base + "?view=system&period=2024-05&source=synthetic")
            run("wait", ".service-row")
            check(
                'location.port === "8504" && new URLSearchParams(location.search).get("period") === "2024-05"'
            )
            check(
                'document.querySelector("nav [data-view=reports]").href.includes("source=synthetic")'
            )
            for tab in ("services", "containers", "guide"):
                run("click", "#tab-" + tab)
                check(
                    f'document.querySelector("#{tab}").checkVisibility() && document.querySelectorAll("[role=tabpanel]:not([hidden])").length === 1 && location.hash === "#{tab}"'
                )
                check("document.documentElement.scrollWidth === innerWidth")
                run("eval", 'document.querySelector(".admin-tabs").scrollIntoView()')
                screenshot(f"admin-{tab}-{width}")
                audit()
            run("focus", "#tab-services")
            run("press", "ArrowRight")
            check(
                'document.activeElement.id === "tab-containers" && !document.querySelector("#containers").hidden'
            )
            run("press", "End")
            check('document.activeElement.id === "tab-guide"')
            run("press", "Home")
            run("click", '[data-action="database-stop"]')
            run("wait", "dialog[open]")
            check('document.activeElement.id === "cancel-action"')
            run("press", "Escape")
            check('!document.querySelector("dialog").open')

        if args.selectors_only:
            complete()
            return

        run("set", "viewport", "1440", "1000", "2")
        run("open", base + "?view=reports&period=2024-04&source=public&plant=PS_001")
        run("wait", ".report-sheet")
        check(
            'document.querySelector("nav [data-view=system]").href.startsWith("http://127.0.0.1:8504/")'
        )
        run("click", "nav [data-view=system]")
        run("wait", ".admin-tabs")
        check('location.port === "8504"')
        run("open", admin + "?period=2024-04&source=public#containers")
        run("wait", "#container-list table")
        check('!document.querySelector("#containers").hidden')

        # Browser-only regression: null, true zero, single point, absent timestamp.
        fixture = {
            "items": [
                {
                    "ts_utc": "2024-04-30T00:00:00+00:00",
                    "power_kw": 0,
                    "poa_wm2": None,
                    "assessment": "INSUFFICIENT_DATA",
                },
                {
                    "ts_utc": "2024-04-30T00:15:00+00:00",
                    "power_kw": None,
                    "poa_wm2": 0,
                    "assessment": "INSUFFICIENT_DATA",
                },
                {
                    "ts_utc": "2024-04-30T00:30:00+00:00",
                    "power_kw": 1,
                    "poa_wm2": None,
                    "assessment": "INSUFFICIENT_DATA",
                },
                {
                    "ts_utc": "2024-04-30T01:00:00+00:00",
                    "power_kw": 2,
                    "poa_wm2": 3,
                    "assessment": "INSUFFICIENT_DATA",
                },
            ]
        }
        run("network", "route", "**/api/v1/plants/PS_001/series*", "--body", json.dumps(fixture))
        run("open", series_url)
        run("wait", ".observation-chart circle")
        check(
            'document.querySelectorAll("circle[data-series=power_kw]").length === 3 && document.querySelectorAll("circle[data-series=poa_wm2]").length === 2 && document.querySelectorAll(".observation-chart polyline").length === 0'
        )
        check('document.querySelector(".observation-summary").textContent.includes("전력 1 / 4")')
        screenshot("fixture-null-zero-single-point")
        run("network", "unroute")
        run("network", "route", "**/api/v1/plants/PS_001/series*", "--body", '{"items":[]}')
        run("reload")
        run("wait", ".empty")
        check('!document.querySelector(".observation-chart")')
        run("network", "unroute")
        run("network", "route", "**/api/v1/plants/PS_001/series*", "--abort")
        run("reload")
        run("wait", ".error")
        run("network", "unroute")
        run("click", ".error button")
        run("wait", ".observation-chart")
        complete()
    finally:
        run("close")


if __name__ == "__main__":
    main()
