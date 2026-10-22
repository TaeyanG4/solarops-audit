"""Package only Git-eligible source. Data, credentials, runtimes and logs stay local."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = (
    subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
    )
    .decode()
    .split("\0")
)
target = root / "SolarOps_Audit_Implementation_v0.1.0.zip"
manifest = {}
with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as z:
    for name in sorted(set(p for p in paths if p)):
        path = Path(name)
        if (
            path.name == ".env"
            or path.suffix == ".zip"
            or path.parts[0] in {"data", "artifacts", ".tools", ".venv", ".venv-linux"}
            or name.startswith("infra/generated/")
        ):
            raise ValueError("Unexpected private/generated file in source inventory")
        content = (root / path).read_bytes()
        manifest[name] = hashlib.sha256(content).hexdigest()
        z.writestr("solarops-audit/" + path.as_posix(), content)
    z.writestr("solarops-audit/SOURCE_MANIFEST.json", json.dumps(manifest, indent=2))
print(
    json.dumps(
        {
            "archive": str(target),
            "files": len(manifest),
            "bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        },
        indent=2,
    )
)
