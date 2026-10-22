#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p .tools
if [[ ! -f .tools/kind ]]; then
  curl -fL https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-linux-amd64 -o .tools/kind
fi
printf '%s\n' 'aee6151561422756b764a4ae28e7f44cda5af5a9eead3cc9985112b1de8d8e0d  .tools/kind' | sha256sum -c -
chmod +x .tools/kind
if [[ ! -f .tools/helm.tar.gz ]]; then
  curl -fL https://get.helm.sh/helm-v3.19.0-linux-amd64.tar.gz -o .tools/helm.tar.gz
fi
printf '%s\n' 'a7f81ce08007091b86d8bd696eb4d86b8d0f2e1b9f6c714be62f82f96a594496  .tools/helm.tar.gz' | sha256sum -c -
if [[ ! -f .tools/linux-amd64/helm ]]; then
  tar -xzf .tools/helm.tar.gz -C .tools
fi
.tools/kind version
.tools/linux-amd64/helm version --short
command -v kubectl >/dev/null || { echo 'Install kubectl from https://kubernetes.io/docs/tasks/tools/ first.'; exit 1; }
