import uuid
from pathlib import Path

import pytest

from solarops.config import Settings
from solarops.fixtures import generate


def pytest_configure(config):
    # Isolate temporary fixtures from system/user temp folders; preserve past evidence.
    if config.option.basetemp is None:
        root = Path("artifacts/test-tmp")
        root.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(root / uuid.uuid4().hex)


@pytest.fixture
def settings(tmp_path):
    return Settings(
        root=tmp_path / "data",
        database_url="sqlite:///" + (tmp_path / "catalog.db").as_posix(),
        s3_endpoint=None,
    )


@pytest.fixture
def sample(tmp_path):
    return generate(tmp_path / "sample")
