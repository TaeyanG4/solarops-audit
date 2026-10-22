import hashlib
import importlib.util
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "package_source", Path(__file__).resolve().parents[1] / "scripts/release/package_source.py"
)
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "pyproject.toml").write_text('[project]\nversion = "9.8.7"\n')
    (root / ".gitignore").write_text(".env*\n!.env.example\n*.zip\ndata/\n")
    (root / ".env.example").write_text("EXAMPLE=placeholder")
    (root / ".env").write_text("LOCAL_SECRET=never-package")
    (root / "data").mkdir()
    (root / "data/raw.csv").write_text("private input")
    return root


def test_archive_version_manifest_and_preserved_output(repository):
    result = packaging.package(repository)
    target = Path(result["archive"])
    assert target.name == "SolarOps_Audit_Implementation_v9.8.7.zip"
    with zipfile.ZipFile(target) as archive:
        manifest = json.loads(archive.read("solarops-audit/SOURCE_MANIFEST.json"))
        assert ".env.example" in manifest
        assert ".env" not in manifest and "data/raw.csv" not in manifest
        for name, digest in manifest.items():
            assert hashlib.sha256(archive.read("solarops-audit/" + name)).hexdigest() == digest
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        packaging.package(repository)
    assert target.read_bytes() == before
    assert Path(packaging.package(repository, repository / "custom.zip")["archive"]).exists()


@pytest.mark.parametrize("name", [".ENV.production", "data/raw.csv"])
def test_forced_private_inventory_rejected_before_output(repository, name):
    if name.lower().startswith(".env"):
        (repository / name).write_text("secret")
    subprocess.run(["git", "add", "-f", name], cwd=repository, check=True)
    with pytest.raises(ValueError, match="private/generated"):
        packaging.package(repository)
    assert list(repository.glob("*.zip")) == []


def test_deleted_tracked_files_are_omitted(repository):
    path = repository / "old.py"
    path.write_text("# old location")
    subprocess.run(["git", "add", "old.py"], cwd=repository, check=True)
    path.rename(repository / "new.py")
    result = packaging.package(repository)
    with zipfile.ZipFile(result["archive"]) as archive:
        assert "solarops-audit/new.py" in archive.namelist()
        assert "solarops-audit/old.py" not in archive.namelist()
