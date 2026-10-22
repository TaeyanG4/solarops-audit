"""Read-only UI regression against a running demo (Agent Browser 0.39.1).

Browser-only fixtures never write API data. Requires an existing public April 2024
and synthetic demo. Not part of offline pytest; does not fetch raw datasets.
"""

import argparse
import json
import os
import shutil
import subprocess
import urllib.request
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8502/")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary = os.environ.get("AGENT_BROWSER_BIN") or shutil.which("agent-browser")
    if binary and Path(binary).suffix.lower() in {".cmd", ".ps1"}:
        # Invoke the native binary directly: cmd wrappers misparse URL ampersands.
        binary = str(
            Path(binary).parent / "node_modules/agent-browser/bin/agent-browser-win32-x64.exe"
        )
    if not binary or not Path(binary).is_file():
        parser.error("Install agent-browser or set AGENT_BROWSER_BIN to its native binary")
    session = f"solarops-check-{uuid.uuid4().hex[:8]}"
    log = []

    def run(*command):
        # A cold Windows daemon can inherit pipe handles. Files avoid waiting for
        # the long-lived daemon to close a parent's subprocess capture pipe.
        stdout_path = args.output / "command-output.json"
        with (
            stdout_path.open("w", encoding="utf-8") as stdout,
            (args.output / "command-error.txt").open("w", encoding="utf-8") as stderr,
        ):
            process = subprocess.run(
                [binary, "--session", session, "--json", *command],
                stdout=stdout,
                stderr=stderr,
                timeout=50,
            )
        result = json.loads(stdout_path.read_text(encoding="utf-8"))
        log.append({"command": list(command), "result": result})
        (args.output / "browser-checks.json").write_text(
            json.dumps(log, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        assert process.returncode == 0 and result.get("success"), result
        return result.get("data")

    def evaluate(js):
        return run("eval", js)["result"]

    def check(js):
        assert evaluate(js) is True, js

    base = args.url.rstrip("/") + "/"
    url = base + "?view=overview&period=2024-04&source=public"
    with urllib.request.urlopen(
        base + "api/v1/overview?period=2024-04&source_kind=public", timeout=20
    ) as response:
        original = json.load(response)
    try:
        run("open", url)
        run("wait", ".energy-chart")
        check('document.querySelectorAll(".plant-table tbody tr").length === 5')
        check(
            'document.querySelector(".provenance a").href === "https://zenodo.org/records/21511487"'
        )
        run("click", '[data-review="partial"]')
        check(
            'document.querySelectorAll(".plant-table tbody tr").length === 1 && document.querySelector(".plant-table").textContent.includes("PS_005")'
        )
        run("fill", ".search", " PS_005 ")
        run("reload")
        run("wait", ".plant-table")
        check(
            'document.querySelector("[data-review=partial]").getAttribute("aria-pressed") === "true" && document.querySelector(".search").value === " PS_005 "'
        )
        run("click", '[aria-label="PS_005 관측 보기"]')
        run("wait", ".chart")
        run("back")
        run("wait", ".plant-table")
        check(
            'location.search.includes("review=partial") && document.querySelectorAll(".plant-table tbody tr").length === 1'
        )
        run("click", ".filter-reset")
        check(
            'document.activeElement === document.querySelector(".search") && document.querySelectorAll(".plant-table tbody tr").length === 5'
        )
        run("click", "[data-review=missing]")
        check('document.querySelector(".filter-empty") !== null')
        run("click", ".filter-reset")
        run("focus", "[data-review=invalid]")
        run("press", "Space")
        check(
            'document.querySelector("[data-review=invalid]").getAttribute("aria-pressed") === "true"'
        )
        run("fill", ".search", "unknown")
        check('document.querySelector(".filter-empty") !== null')
        run("click", ".filter-reset")
        run("focus", ".day-mark")
        run("press", "ArrowRight")
        check('document.querySelector(".chart-controls select").value === "1"')
        run("press", "End")
        check('document.querySelector(".chart-step:last-child").disabled')
        run("select", ".chart-controls select", "9")
        check('document.querySelector(".day-inspector").textContent.includes("22.95 MWh")')
        run("click", ".chart-data summary")
        check('document.querySelectorAll(".chart-data tbody tr").length === 30')
        run("click", ".chart-data summary")
        run("click", '[aria-label="PS_001 관측 보기"]')
        run("wait", ".chart")
        run("click", "[data-view=reports]")
        run("wait", ".report-sheet")
        check(
            '!document.querySelector("iframe") && document.querySelector(".report-sheet").textContent.includes("585,980.28")'
        )
        run("click", "[data-view=runs]")
        run("wait", ".filters")
        run("click", "[data-view=overview]")
        run("wait", ".energy-chart")
        run("select", "#source", "all")
        run("wait", ".energy-chart")
        check('document.querySelector(".provenance h2").textContent.includes("함께 조회")')
        run("select", "#source", "synthetic")
        run("wait", ".energy-chart")
        check(
            'document.querySelector(".provenance h2").textContent.includes("합성") && !document.querySelector(".provenance a")'
        )
        run("select", ".chart-controls select", "29")
        check('document.querySelector(".day-inspector strong").textContent === "자료 없음"')
        run("click", "[data-review=missing]")
        check('document.querySelectorAll(".plant-table tbody tr").length === 1')
        run("open", base + "?view=overview&period=1990-01&source=public")
        run("wait", ".empty")
        check(
            'document.querySelector(".empty").textContent.includes("0 발전량으로 처리하지 않습니다")'
        )
        run("open", url)
        run("wait", ".energy-chart")
        fixture = json.loads(json.dumps(original))
        fixture["summary"]["estimated_energy_kwh"] = None
        fixture["plants"][0]["estimated_energy_kwh"] = None
        fixture["plants"][1]["estimated_energy_kwh"] = 0
        fixture["timeline"][0]["metrics"]["estimated_energy_kwh"] = 0
        fixture["timeline"][1]["metrics"] = None
        fixture["timeline"][2]["metrics"]["estimated_energy_kwh"] = None
        run("network", "route", "**/api/v1/overview*", "--body", json.dumps(fixture))
        run("click", "#refresh")
        run("wait", ".energy-chart")
        check('document.querySelector(".card-value").textContent === "추정값 없음"')
        check(
            'document.querySelector(".plant-table tbody tr td:nth-child(3)").textContent === "추정값 없음"'
        )
        check(
            'document.querySelector(".plant-table tbody tr:nth-child(2) td:nth-child(3)").textContent === "0"'
        )
        for index, expected in ((0, "0 MWh"), (1, "자료 없음"), (2, "추정값 없음")):
            run("select", ".chart-controls select", str(index))
            assert (
                evaluate('document.querySelector(".day-inspector strong").textContent') == expected
            )
        check(
            'document.querySelectorAll(".unknown-mark").length === 1 && document.querySelectorAll(".missing-mark").length === 1'
        )
        run("click", ".chart-data summary")
        check(
            'document.querySelector(".chart-data tbody tr:nth-child(3)").textContent.includes("추정값 없음")'
        )
        run("set", "viewport", "390", "1000", "2")
        check("document.documentElement.scrollWidth === innerWidth")
        run("screenshot", str(args.output / "null-zero-missing.png"), "--full")
        run("network", "unroute")
        run("network", "route", "**/api/v1/overview*", "--abort")
        run("click", "#refresh")
        run("wait", ".error")
        run("screenshot", str(args.output / "error.png"))
        run("network", "unroute")
        run("click", ".error button")
        run("wait", ".energy-chart")
        for width in (1440, 768, 390):
            run("set", "viewport", str(width), "1000", "2")
            check("document.documentElement.scrollWidth === innerWidth")
            audit = run("a11y")
            assert audit["counts"]["violations"] == 0, audit
            run("screenshot", str(args.output / f"after-{width}.png"), "--full")
            run("screenshot", str(args.output / f"viewport-{width}.png"))
        run("set", "viewport", "320", "900")
        check("document.documentElement.scrollWidth === innerWidth")
        run("set", "media", "light", "reduced-motion")
        check('getComputedStyle(document.querySelector("#refresh")).transitionDuration === "0s"')
        run("errors")
        run("console")
        with urllib.request.urlopen(
            base + "api/v1/overview?period=2024-04&source_kind=public", timeout=20
        ) as response:
            assert json.load(response) == original
        (args.output / "result.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "browser_commands": len(log),
                    "axe_viewports": [1440, 768, 390],
                    "fixtures": "browser only; null vs zero vs missing; network abort",
                    "api_unchanged": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"PASS: {len(log)} browser commands, 3 axe audits, API unchanged")
    finally:
        run("close")


if __name__ == "__main__":
    main()
