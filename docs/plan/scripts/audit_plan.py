"""Structural QA for the SolarOps Audit planning bundle; no network required."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "00_START_HERE.md", "01_MASTER_PRD.md", "02_CODEX_EXECUTION.md",
    "03_BUSINESS_PILOT.md", "04_REVIEW_SESSION_PROMPT.md",
    "05_REVIEW_RESULTS.md", "AGENTS.md",
]
issues = []
for name in REQUIRED:
    path = ROOT / name
    if not path.is_file():
        issues.append(f"Missing file: {name}")
        continue
    text = path.read_text(encoding="utf-8")
    if not text.strip().startswith("# "):
        issues.append(f"Missing top heading: {name}")
    fences = len(re.findall(r"^```", text, re.MULTILINE))
    if fences % 2:
        issues.append(f"Unclosed Markdown code fence: {name}")
master = (ROOT / "01_MASTER_PRD.md").read_text(encoding="utf-8")
execution = (ROOT / "02_CODEX_EXECUTION.md").read_text(encoding="utf-8")
expected = [
    ("Master/BR-PVGen", master, "https://zenodo.org/records/21511487"),
    ("Master/interpolation", master, "interpolated_keys_*"),
    ("Master/data lineage", master, "source_object"),
    ("Master/org boundary", master, "UNIQUE(org_id, sha256)"),
    ("Master/canonical hash", master, "논리 데이터 해시"),
    ("Master/atomic publishing", master, "active_partition_manifest"),
    ("Master/Airflow", master, "KubernetesPodOperator"),
    ("Master/K8s", master, "kind"),
    ("Master/Helm", master, "Helm"),
    ("Master/energy unit", master, "0.25h"),
    ("Master/limited diagnosis", master, "고장 확정"),
    ("Execution/M0", execution, "### M0"),
    ("Execution/M9", execution, "### M9"),
    ("Execution/no download", execution, "make download-full"),
]
for label, doc, needle in expected:
    if needle not in doc:
        issues.append(f"Missing: {label}, expected {needle}")
for text, name in [(master, "Master"), (execution, "Execution")]:
    for bad in ["TODO FIXME", "임시로 허위"]:
        if bad in text:
            issues.append(f"Suspicious placeholder in {name}: {bad}")
print(f"Checked {len(REQUIRED)} planning documents and {len(expected)} required anchors")
if issues:
    for issue in issues:
        print("FAIL:", issue)
    raise SystemExit(1)
print("PASS: document structure and required contract anchors")
