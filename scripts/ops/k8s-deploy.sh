#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PATH="$PWD/.tools:$PWD/.tools/linux-amd64:$PATH"
export KUBECONFIG="$PWD/artifacts/kubeconfig"
python3 scripts/ops/k8s-secrets.py
kind load docker-image --name solarops solarops-worker:0.4.1 solarops-airflow:0.4.1 solarops-minio:2025-10-15
kubectl apply -f infra/k8s/services.yaml
kubectl apply -f infra/k8s/logs.yaml
kubectl apply -f infra/generated/secrets.json
kubectl rollout status -n solarops deployment/app-db --timeout=180s
kubectl rollout status -n solarops deployment/minio --timeout=180s
kubectl rollout status -n solarops deployment/airflow-db --timeout=180s
helm repo add apache-airflow https://airflow.apache.org --force-update
helm repo update apache-airflow
helm template airflow apache-airflow/airflow --version 1.22.0 -n solarops -f infra/helm/airflow-values.yaml > artifacts/helm-rendered.yaml
helm upgrade --install airflow apache-airflow/airflow --version 1.22.0 -n solarops -f infra/helm/airflow-values.yaml --timeout 10m
kubectl get pods -n solarops
