import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

CALCULATION_VERSION = "energy-interval-v2"
SCHEMA_VERSION = "1"


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
        raise ValueError("Identifier must contain only letters, digits, underscore or hyphen")
    return value


@dataclass
class Settings:
    root: Path = field(
        default_factory=lambda: Path(os.getenv("SOLAROPS_DATA_DIR", "data")).resolve()
    )
    database_url: str | None = field(default_factory=lambda: os.getenv("SOLAROPS_DATABASE_URL"))
    org: str = field(default_factory=lambda: os.getenv("SOLAROPS_ORG", "demo"))
    timezone: str = field(default_factory=lambda: os.getenv("SOLAROPS_REPORT_TIMEZONE", "UTC"))
    s3_endpoint: str | None = field(default_factory=lambda: os.getenv("SOLAROPS_S3_ENDPOINT"))
    source_root: Path = field(
        default_factory=lambda: Path(os.getenv("SOLAROPS_SOURCE_DIR", "data/source")).resolve()
    )

    def __post_init__(self):
        identifier(self.org)
        ZoneInfo(self.timezone)
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.database_url:
            self.database_url = "sqlite:///" + (self.root / "solarops.db").as_posix()
