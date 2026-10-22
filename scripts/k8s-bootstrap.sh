#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools:$PWD/.tools/linux-amd64:$PATH"
mkdir -p artifacts
if ! kind get clusters | grep -qx solarops; then
  kind create cluster --name solarops --config infra/kind/cluster.yaml --wait 180s
fi
kind get kubeconfig --name solarops > artifacts/kubeconfig
export KUBECONFIG="$PWD/artifacts/kubeconfig"
kubectl cluster-info
