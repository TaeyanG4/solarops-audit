#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/ops/bootstrap.py
docker compose --env-file .env -f infra/compose/compose.yaml build dashboard minio
docker compose --env-file .env -f infra/compose/compose.yaml run --rm --no-deps --user 0:0 --entrypoint python worker -c 'import os; from pathlib import Path; os.chown("/data",50000,0); os.chmod("/data",0o1777); Path("/data/.initialized").touch()'
docker compose --env-file .env -f infra/compose/compose.yaml up -d app-db minio dashboard
# Fresh install: create the catalog schema and bucket so /ready passes before any demo run.
for attempt in $(seq 1 30); do
  if docker compose --env-file .env -f infra/compose/compose.yaml run --rm worker db-migrate; then
    exit 0
  fi
  sleep 2
done
echo "db-migrate did not succeed; check app-db and minio logs" >&2
exit 1
