"""Package Git-eligible source after validating the full inventory; never overwrite."""

import argparse
import hashlib
import json
import subprocess
import tomllib
import zipfile
from pathlib import Path


def git_paths(root, *args):
    return set(
        filter(
            None,
            subprocess.check_output(["git", "ls-files", *args, "-z"], cwd=root)
            .decode("utf-8")
            .split("\0"),
        )
    )


def package(root: Path, target: Path | None = None):
    root = root.resolve()
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    target = target or root / f"SolarOps_Audit_Implementation_v{version}.zip"
    if target.suffix.lower() != ".zip":
        raise ValueError("Output must be a .zip file")
    if target.exists():
        raise FileExistsError(
            "Output already exists; select a new path to preserve earlier evidence"
        )
    paths = git_paths(root, "--cached", "--others", "--exclude-standard") - git_paths(
        root, "--deleted"
    )
    contents = {}
    for name in sorted(paths):
        relative = Path(name)
        path = root / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.name.lower() == ".env"
            or (
                relative.name.lower().startswith(".env.")
                and relative.name.lower() != ".env.example"
            )
            or relative.suffix.lower() in {".zip", ".pem", ".key"}
            or relative.parts[0].lower() in {"data", "artifacts", ".tools", ".git"}
            or relative.parts[0].lower().startswith(".venv")
            or name.lower().startswith("infra/generated/")
            or not path.resolve().is_relative_to(root)
            or any(
                p.is_symlink()
                for p in (path, *path.parents)
                if p != root and p.is_relative_to(root)
            )
            or not path.is_file()
        ):
            raise ValueError(
                f"Unexpected private/generated or linked file in source inventory: {name}"
            )
        contents[relative.as_posix()] = path.read_bytes()
    # Validate everything before creating an output file, including ignored-but-tracked secrets.
    manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in contents.items():
            archive.writestr("solarops-audit/" + name, content)
        archive.writestr("solarops-audit/SOURCE_MANIFEST.json", json.dumps(manifest, indent=2))
    return {
        "archive": str(target.resolve()),
        "version": version,
        "files": len(manifest),
        "bytes": target.stat().st_size,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="New ZIP path; default uses pyproject.toml version"
    )
    args = parser.parse_args()
    print(json.dumps(package(Path(__file__).resolve().parents[2], args.output), indent=2))


if __name__ == "__main__":
    main()
