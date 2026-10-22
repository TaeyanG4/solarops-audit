import os
import subprocess
import sys
from pathlib import Path

values = dict(
    line.split("=", 1)
    for line in Path(".env").read_text().splitlines()
    if line and not line.startswith("#")
)
env = dict(
    os.environ,
    SOLAROPS_DATABASE_URL=f"postgresql+psycopg://solarops:{values['APP_DB_PASSWORD']}@127.0.0.1:55432/solarops",
    SOLAROPS_S3_ENDPOINT="http://127.0.0.1:59000",
    SOLAROPS_S3_ACCESS_KEY=values["MINIO_ROOT_USER"],
    SOLAROPS_S3_SECRET_KEY=values["MINIO_ROOT_PASSWORD"],
    SOLAROPS_TEST_SERVICES="1",
)
sys.exit(
    subprocess.call(
        [sys.executable, "-m", "pytest", "tests/test_services.py", "-q", "--tb=short"], env=env
    )
)
