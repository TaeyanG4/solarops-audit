"""Explicit, bounded downloads. No fetching during installation or tests."""

import hashlib
import json
import os
import shutil
import urllib.request
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

RECORD = "https://zenodo.org/api/records/21511487"
DOI = "https://doi.org/10.5281/zenodo.21511487"
FILES = {
    "Readme.txt",
    "BR-PVGen_metadata.csv",
    "BR-PVGen_inverter.zip",
    "BR-PVGen_meteorological.zip",
}
MAX_DOWNLOAD = 400_000_000
MAX_EXPANDED = 8_000_000_000


def checksum(path: Path, algorithm="sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inspect_source():
    with urllib.request.urlopen(RECORD, timeout=60) as response:
        return json.load(response)


def fetch(destination: Path, names: list[str], allow_large=False):
    if not set(names) <= FILES:
        raise ValueError("Unknown source file")
    record = inspect_source()
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for item in record["files"]:
        name = item["key"]
        if name not in names:
            continue
        if item["size"] > MAX_DOWNLOAD or (item["size"] > 1_000_000 and not allow_large):
            raise ValueError("Large download requires --allow-large")
        target = destination / name
        expected = item["checksum"].removeprefix("md5:")
        if target.exists():
            if checksum(target, "md5") != expected:
                raise ValueError(
                    f"Existing source differs: {name}; preserve it and use a new directory"
                )
        else:
            temporary = destination / (name + ".partial-" + uuid.uuid4().hex)
            size = 0
            with (
                urllib.request.urlopen(item["links"]["self"], timeout=120) as response,
                temporary.open("xb") as out,
            ):
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(block)
                    if size > item["size"] or size > MAX_DOWNLOAD:
                        raise ValueError("Download exceeds declared limit")
                    out.write(block)
            if size != item["size"] or checksum(temporary, "md5") != expected:
                raise ValueError("Source size/checksum mismatch; partial retained for inspection")
            os.replace(temporary, target)
        manifest = {
            "org_id": "demo",
            "origin_url": item["links"]["self"],
            "upstream_dataset_version": record["metadata"]["version"],
            "original_filename": name,
            "md5_expected": expected,
            "sha256_actual": checksum(target),
            "byte_size": target.stat().st_size,
            "license": "CC BY 4.0",
            "downloaded_at_utc": datetime.now(UTC).isoformat(),
            "source_kind": "public",
            "source_preprocessed": True,
            "doi": DOI,
        }
        manifest_path = destination / (name + ".manifest.json")
        if not manifest_path.exists():
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        results.append(manifest)
    (destination / "record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return results


def safe_extract(archive: Path, destination: Path, limit=MAX_EXPANDED):
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as z:
        total = 0
        for item in z.infolist():
            p = PurePosixPath(item.filename.replace("\\", "/"))
            if p.is_absolute() or ".." in p.parts or ":" in item.filename:
                raise ValueError("Unsafe ZIP path")
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("ZIP symlinks are forbidden")
            if not item.is_dir() and p.suffix.lower() != ".csv":
                raise ValueError("ZIP may contain only CSV files")
            total += item.file_size
            if total > limit or (
                item.file_size > 1_000_000 and item.file_size > max(item.compress_size, 1) * 1000
            ):
                raise ValueError("ZIP expansion exceeds limit")
        for item in z.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Unsafe ZIP target")
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                # Never overwrite previously extracted inputs.
                with z.open(item) as source:
                    incoming = hashlib.file_digest(source, "sha256").hexdigest()
                if checksum(target) != incoming:
                    raise ValueError("Existing extracted data differs")
                continue
            # Each CSV becomes visible only after EOF/CRC, size and fsync succeed.
            # Retain staging evidence (including interrupted copies); never overwrite
            # a concurrent extractor's completed file or a pre-existing raw input.
            staged = target.with_name(target.name + ".partial-" + uuid.uuid4().hex)
            with z.open(item) as source, staged.open("xb") as out:
                shutil.copyfileobj(source, out, 1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            if staged.stat().st_size != item.file_size:
                raise ValueError("Extracted size mismatch; partial retained")
            try:
                os.link(staged, target)
            except FileExistsError:
                if checksum(target) != checksum(staged):
                    raise ValueError("Existing extracted data differs") from None
    return {"expanded_bytes": total, "destination": str(destination)}
