"""Render secrets to ignored private files, never stdout."""

import base64
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = dict(
    line.split("=", 1)
    for line in (root / ".env").read_text().splitlines()
    if line and not line.startswith("#")
)
db = f"postgresql+psycopg://solarops:{env['APP_DB_PASSWORD']}@app-db.solarops.svc.cluster.local:5432/solarops"
app = {
    "SOLAROPS_DATABASE_URL": db,
    "SOLAROPS_S3_ENDPOINT": "http://minio.solarops.svc.cluster.local:9000",
    "SOLAROPS_S3_ACCESS_KEY": env["MINIO_ROOT_USER"],
    "SOLAROPS_S3_SECRET_KEY": env["MINIO_ROOT_PASSWORD"],
    "SOLAROPS_S3_BUCKET": "solarops-demo",
    "SOLAROPS_ORG": "demo",
}
secrets = {
    "solarops-infra": env,
    "solarops-app": app,
    "airflow-metadata": {
        "connection": f"postgresql://airflow:{env['AIRFLOW_DB_PASSWORD']}@airflow-db.solarops.svc.cluster.local:5432/airflow"
    },
    "airflow-fernet": {"fernet-key": env["AIRFLOW_FERNET_KEY"]},
    "airflow-jwt": {"jwt-secret": env["AIRFLOW_JWT_SECRET"]},
    "airflow-webserver": {"webserver-secret-key": env["AIRFLOW_JWT_SECRET"]},
}
objects = [
    {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": name, "namespace": "solarops"},
        "type": "Opaque",
        "data": {k: base64.b64encode(v.encode()).decode() for k, v in values.items()},
    }
    for name, values in secrets.items()
]
out = root / "infra/generated/secrets.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"apiVersion": "v1", "kind": "List", "items": objects}), encoding="utf-8")
out.chmod(0o600)
print("Generated ignored Kubernetes secret file")
