"""Check repository-local Markdown links, script references and archived plan bytes.

External URLs and Markdown heading fragments are intentionally not fetched/validated.
"""

import hashlib
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main():
    root = Path(__file__).resolve().parents[2]
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
        )
        .decode("utf-8")
        .split("\0")
    )
    errors, links, references = [], 0, 0
    for name in sorted(set(paths)):
        path = root / name
        if not name or not path.is_file() or name.startswith("docs/plan/"):
            continue
        if path.suffix not in {".md", ".py", ".sh", ".yaml", ".yml"} and name != "Makefile":
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            for match in re.finditer(r"\]\(([^\s)]+)\)", text):
                target = urlsplit(match[1].strip("<>"))
                if target.scheme or target.netloc or not target.path:
                    continue
                links += 1
                resolved = (path.parent / unquote(target.path)).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    errors.append(f"{name}: broken local link {match[1]}")
        for match in re.finditer(r"(?<![\w/])scripts/([A-Za-z0-9_./-]+\.(?:py|sh))", text):
            references += 1
            if not (root / match[0]).is_file():
                errors.append(f"{name}: missing script {match[0]}")
    archive = root / "docs/plan"
    for line in (archive / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        if hashlib.sha256((archive / name).read_bytes()).hexdigest() != digest:
            errors.append(f"Archived plan checksum changed: {name}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"Documentation OK: {links} local links, {references} script references, 8 archived checksums"
    )


if __name__ == "__main__":
    main()
