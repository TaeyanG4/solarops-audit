import os
import uuid
from pathlib import Path

import pytest

from solarops.config import Settings
from solarops.storage.minio import ObjectStore
from solarops.storage.postgres import Catalog
from tests.test_pipeline import run


@pytest.mark.services
@pytest.mark.skipif(
    not os.getenv("SOLAROPS_TEST_SERVICES"), reason="Explicit Postgres/MinIO integration opt-in"
)
def test_postgres_minio_transaction(sample, tmp_path):
    settings = Settings(root=tmp_path, org="test-" + uuid.uuid4().hex[:12])
    first = run(settings, sample)
    with pytest.raises(RuntimeError):
        run(settings, sample, fail_at="during_commit")
    second = run(settings, sample)
    assert [r["logical_hash"] for r in first["results"]] == [
        r["logical_hash"] for r in second["results"]
    ]
    snapshot = Catalog(settings).snapshot(settings.org)
    store = ObjectStore(settings)
    uri = snapshot[0]["payload"]["source_objects"][0]["raw_uri"]
    bucket, key = uri[5:].split("/", 1)
    assert (
        store.client.head_object(Bucket=bucket, Key=key)["ContentLength"]
        == Path(sample["metadata"]).stat().st_size
    )
