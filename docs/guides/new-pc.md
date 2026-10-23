# 새 PC에서 전체 기술 스택 재현하기

[프로젝트 홈](../../README.md) · [설치 상세](setup.md) · [운영 절차](../runbooks/operator.md) · [DAG 운영](../runbooks/dags.md)

포맷한 Windows PC에서 이 프로젝트의 기술 스택(Python CLI, Docker Compose의 PostgreSQL·MinIO·대시보드·Airflow, kind 쿠버네티스의 Airflow + KubernetesPodOperator, ONS 실제 수집)을 처음부터 다시 띄우는 순서입니다. 같은 명령을 빈 Ubuntu 머신에서 자동으로 실행하는 [재현 workflow](../../.github/workflows/reproduce.yaml)가 2026-10-23에 전 단계를 통과했습니다([실행 기록](https://github.com/TaeyanG4/solarops-audit/actions/runs/39965762056)). Windows 고유 단계(1·2단계의 WSL·Docker Desktop 설치)는 이 자동 검증 범위 밖입니다.

옮겨지지 않는 것: 이전 PC의 ONS 수집 이력, 발행 보고서 이력, Git 제외 로컬 기록(`artifacts/`, `data/`). 비밀값(`.env`)은 새 PC에서 무작위로 새로 만듭니다. 공개 BR-PVGen 전체 결과는 원본을 다시 내려받아 처리하면 같은 계산 결과(논리 해시)가 나옵니다.

## 1. Windows 준비 (PowerShell 관리자)

BIOS의 가상화가 켜져 있어야 합니다.

```powershell
wsl --install -d Ubuntu-22.04
```

재부팅 후 Ubuntu 사용자 이름/암호를 만듭니다. 그다음 [Docker Desktop](https://www.docker.com/products/docker-desktop/)을 설치하고 **Settings → Resources → WSL integration**에서 `Ubuntu-22.04`를 켭니다. kind와 Compose를 함께 띄우려면 Docker(WSL2)에 메모리 8GB 이상을 권장합니다.

## 2. Ubuntu(WSL) 안의 도구

```bash
sudo apt update && sudo apt install -y git make curl python3
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
curl -fLO https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl
sudo install -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl
docker version && kubectl version --client && uv --version
```

kind 0.33.0과 Helm 3.19.0은 5단계의 스크립트가 SHA-256을 확인해 저장소의 `.tools/`에 받습니다.

## 3. 저장소 받기

WSL 파일 시스템(`~`)에 받는 것이 Windows 드라이브(`/mnt/c`)보다 빠릅니다. `main`은 앱 릴리스 0.5.7과 이 재현 절차(ONS 명령 포함)를 담고 있으며, 재현 workflow가 검증하는 기준입니다.

```bash
cd ~
git clone https://github.com/TaeyanG4/solarops-audit.git
cd solarops-audit
export UV_PROJECT_ENVIRONMENT=.venv-linux   # make와 uv run이 같은 가상환경을 쓰도록
make install
uv run python scripts/demo/portfolio_demo.py --serve
```

`http://127.0.0.1:8503/`에서 실패 보존·재처리 결과를 확인하고 Ctrl+C로 끕니다.

## 4. Docker Compose + Airflow + ONS

```bash
make up-local          # .env 비밀값 생성 → 이미지 빌드(MinIO는 고정 소스 빌드) → 기동 → DB 스키마·버킷 준비
make demo-services     # 실제 PostgreSQL·MinIO로 합성 데모
make test-services     # 실제 서비스 검사 13개
make ons-sync          # ONS 지난달·이번 달 실제 수집(인터넷 필요)
make ons-status        # 이번 달 수집 상태
make airflow-up        # Compose Airflow
make dag-validate
uv run python scripts/validation/airflow_checks.py --mode compose        # 정상·재시도·백필·품질·보고서 DAG
uv run python scripts/validation/airflow_checks.py --mode compose --ons  # ONS DAG
```

확인: 대시보드 `http://127.0.0.1:8502`, Airflow `http://127.0.0.1:8080`(로컬 개발용, 인증 없음). 메모리가 작으면 kind 전에 `make down-local`로 Compose를 중지합니다(볼륨 유지).

## 5. Kubernetes (kind + Airflow + KPO + ONS)

```bash
bash scripts/ops/install-k8s-tools.sh
make k8s-bootstrap     # kind 클러스터 solarops 생성
make k8s-deploy        # 이미지를 kind에 넣고 Airflow를 Helm으로 배포
make k8s-smoke         # 합성 DAG를 KPO 작업 Pod로 실행
uv run python scripts/validation/airflow_checks.py --mode k8s --ons     # ONS DAG를 KPO로 실제 수집
export KUBECONFIG="$PWD/artifacts/kubeconfig"
kubectl get pods -n solarops
```

`airflow-api-server`, `airflow-scheduler`, `airflow-dag-processor`, `airflow-db`, `app-db`, `minio` 6개 Pod가 Running이면 됩니다. ONS를 매일 14:00 KST에 자동 수집하려면 [DAG 운영](../runbooks/dags.md#ons-정기-수집-켜기끄기)의 `dags unpause solarops_ons_daily`를 실행합니다(기본은 일시중지).

## 6. 선택: 공개 원본 전체 처리

```bash
make download-full     # Zenodo BR-PVGen 약 350MB, 체크섬 확인
uv run python scripts/data/full_dataset.py --services
```

51개 발전소·12,572개 일별 파티션을 처리합니다(작업 PC 기준 약 16분). 결과 대조는 `uv run python scripts/validation/verify_catalogs.py`입니다.

## 끄기와 다시 켜기

```bash
make down-local                         # Compose 중지(볼륨 유지)
docker stop solarops-control-plane      # kind 중지(ONS 정기 수집도 멈춤)
docker compose --env-file .env -f infra/compose/compose.yaml start app-db minio dashboard
docker start solarops-control-plane
```

`solarops-control-plane` 컨테이너와 `solarops-audit_*` 볼륨을 지우면 해당 환경의 자료가 사라집니다.
