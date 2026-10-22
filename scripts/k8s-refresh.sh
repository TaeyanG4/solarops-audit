#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools:$PWD/.tools/linux-amd64:$PATH"
export KUBECONFIG="$PWD/artifacts/kubeconfig"
kind load docker-image --name solarops solarops-airflow:0.2.0 solarops-worker:0.2.0
kubectl annotate pvc airflow-logs -n solarops helm.sh/resource-policy=keep --overwrite || true
kubectl apply -f infra/k8s/logs.yaml
helm upgrade airflow apache-airflow/airflow --version 1.22.0 -n solarops -f infra/helm/airflow-values.yaml --timeout 5m
kubectl rollout restart deployment/airflow-api-server deployment/airflow-dag-processor statefulset/airflow-scheduler -n solarops
