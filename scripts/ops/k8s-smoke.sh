#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export KUBECONFIG="$PWD/artifacts/kubeconfig"
kubectl rollout status statefulset/airflow-scheduler -n solarops --timeout=180s
kubectl rollout status deployment/airflow-dag-processor -n solarops --timeout=180s
python3 scripts/validation/airflow_checks.py --mode k8s
kubectl get pods -n solarops
kubectl exec -n solarops deployment/app-db -- psql -U solarops -d solarops -c 'SELECT count(*) AS active_partitions FROM active_partition_manifest;'
