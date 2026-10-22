#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/ops/bootstrap.py
docker compose --env-file .env -f infra/compose/compose.yaml build dashboard minio
docker compose --env-file .env -f infra/compose/compose.yaml run --rm --no-deps --user 0:0 --entrypoint python worker -c 'import os; from pathlib import Path; os.chown("/data",50000,0); os.chmod("/data",0o1777); Path("/data/.initialized").touch()'
docker compose --env-file .env -f infra/compose/compose.yaml up -d app-db minio dashboard
