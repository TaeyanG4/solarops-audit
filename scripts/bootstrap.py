"""Generate local secrets once. Existing .env is always preserved."""

import base64
import os
import secrets
from pathlib import Path

target = Path(__file__).resolve().parents[1] / ".env"
if target.exists():
    print("Existing .env preserved")
else:
    values = {
        "APP_DB_PASSWORD": secrets.token_hex(24),
        "AIRFLOW_DB_PASSWORD": secrets.token_hex(24),
        "MINIO_ROOT_USER": "solarops-" + secrets.token_hex(6),
        "MINIO_ROOT_PASSWORD": secrets.token_hex(24),
        "AIRFLOW_FERNET_KEY": base64.urlsafe_b64encode(os.urandom(32)).decode(),
        "AIRFLOW_JWT_SECRET": secrets.token_hex(32),
    }
    with target.open("x", encoding="utf-8") as f:
        f.write("\n".join(k + "=" + v for k, v in values.items()) + "\n")
    if os.name != "nt":
        target.chmod(0o600)
    print("Generated .env; secrets are not printed or committed")
