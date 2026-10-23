# 설치와 실행

[문서 홈](../README.md) · [운영 안내](../runbooks/operator.md)

모든 명령은 저장소 루트에서 실행합니다. 네이티브 합성 데모 → Compose → kind 순서로 필요한 단계까지만 진행하세요. 저장소는 비공개이므로 clone에는 허가된 GitHub 계정이 필요합니다. 의존성 최초 설치에는 네트워크가 필요하며, 설치 후 합성 처리는 외부 자료 다운로드 없이 실행됩니다.

## 사전 준비

| 경로 | 필요한 도구 | 확인 명령 |
|---|---|---|
| 네이티브 데모 | Git, [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.12는 uv가 받을 수 있음) | `uv --version` |
| Compose · Airflow | 위 항목 + Docker Engine/Docker Desktop(Linux 엔진), Windows는 WSL2 Ubuntu와 그 안의 `make` · `python3` · `uv` · `curl` | `docker version`, `make --version` |
| Kubernetes (kind) | 위 항목 + [kubectl](https://kubernetes.io/docs/tasks/tools/). kind 0.33.0 · Helm 3.19.0은 `scripts/ops/install-k8s-tools.sh`가 SHA-256을 확인해 `.tools/`에 받음 | `kubectl version --client` |

Compose 첫 실행은 이미지 빌드(특히 MinIO 고정 소스 빌드) 때문에 오래 걸리고 네트워크가 필요합니다. kind는 Compose와 별도로 DB·MinIO·Airflow를 띄우므로 메모리가 작으면 Compose를 중지하고 진행하세요. 이 절차는 작업 PC(Windows + WSL2 Ubuntu 22.04 + Docker Desktop)에서 실행·운영했으며, 빈 머신에서 처음부터 다시 설치하는 검증은 아직 하지 않았습니다.

## 빠른 실행

[Python 3.12](https://www.python.org/downloads/)와 [uv](https://docs.astral.sh/uv/getting-started/installation/), Git이 필요합니다. Windows PowerShell, macOS/Linux 셸에서:

```text
git clone https://github.com/TaeyanG4/solarops-audit.git
cd solarops-audit
uv sync --frozen
uv run solarops doctor
uv run solarops demo
uv run solarops serve
```

[대시보드](http://127.0.0.1:8501) · [API 문서](http://127.0.0.1:8501/docs)

v0.4.1부터 `serve`는 저장소를 생성하지 않습니다. 위의 `demo`가 DB와 자료를 준비합니다. 자료 없이 빈 catalog만 준비하려면 같은 환경 설정에서 `uv run solarops db-migrate`를 먼저 실행하세요. `/health`는 프로세스 상태, `/ready`는 catalog 스키마와 설정된 객체 저장소 접근을 확인합니다. DB/스키마/버킷이 없으면 503이며, 전체 파일의 존재·무결성을 전수 검사하는 API는 아닙니다.

기본 데모는 네트워크나 Docker 없이 합성 데이터 1주를 처리합니다. `data/`에 SQLite 카탈로그, 원본, Parquet, 보고서를 보존합니다. 실행 후 출력되는 `report.html`, `metrics.csv`, `manifest.json`은 브라우저·Excel·JSON 도구에서 볼 수 있습니다.

실패와 복구를 포함한 독립 시연은 `uv run python scripts/demo/portfolio_demo.py --serve`로 실행합니다. 새 디렉터리에 정상 처리 → 커밋 중 실패 → 기존 결과 보존 → 동일 결과 재처리를 확인한 뒤 [8503 대시보드](http://127.0.0.1:8503/)를 제공합니다. 공개 데이터 다운로드는 필요 없습니다.

## WSL2 / Ubuntu

```bash
make install
make doctor
make lint
make test
make demo-sample
make serve
```

Make는 Windows용 `.venv`와 다른 `.venv-linux`를 사용하고, 로컬 DB도 `data/linux-native`로 분리합니다. Windows와 WSL에서 같은 SQLite WAL 파일을 동시에 열지 마세요. Make 명령에는 `make`와 uv가 필요합니다. 인프라 실행에는 Docker Compose가 추가로 필요하며, WSL에서는 Linux 파일시스템의 별도 checkout을 권장합니다.

## PostgreSQL · MinIO · Airflow

Docker Desktop의 Linux 엔진을 실행하고 WSL에서:

```bash
make up-local
make demo-services
make test-services
make airflow-up
make dag-validate
```

- 제품 대시보드: [127.0.0.1:8502](http://127.0.0.1:8502)
- Airflow: [127.0.0.1:8080](http://127.0.0.1:8080)
- 앱 PostgreSQL: localhost:55432. Airflow DB는 별도 컨테이너/계정/볼륨.
- MinIO API: localhost:59000. 암호는 `scripts/ops/bootstrap.py`가 `.env`에 무작위 생성합니다.
- 로컬 UI는 인증 없는 개발용입니다. 모든 호스트 포트는 127.0.0.1에만 바인딩합니다.
- `make down-local`은 컨테이너를 **중지**하며 볼륨을 삭제하지 않습니다.

MinIO 공식 공개 이미지/바이너리 배포가 이 환경에서 접근 불가하여, 공식 저장소의 `RELEASE.2025-10-15T17-29-55Z` 소스를 빌드합니다. 첫 빌드는 Go 의존성 다운로드 때문에 시간이 걸립니다. MinIO는 AGPLv3입니다.

## 공개 자료 처리

설치/테스트에서는 공개 자료를 다운로드하지 않습니다. 아래 명령으로만 내려받습니다.

현재 원천은 고정 BR-PVGen V.1이며 신규 관측값 자동 수집은 없습니다. 다운로드·적재·보고서는 별도 단계입니다. [수집 주기·기존 자료 확장·새 출처 연동](data-ingestion.md)을 먼저 확인하세요. 네이티브 기본 SQLite의 결과는 Compose 8502 화면과 별개이며, 서비스용 명령도 해당 안내에 있습니다.

```bash
make download-metadata
make download-full
uv run solarops ingest \
  --metadata data/source/BR-PVGen_metadata.csv \
  --inverter data/source/inverter/BR-PVGen_inverter/PS_001.csv \
  --station data/source/station/BR-PVGen_meteorological/PS_001.csv \
  --plant PS_001 --from 2024-04-01 --to 2024-04-08 \
  --source-version brpvgen-v1 --source-kind public
uv run solarops report --period 2024-04 --plant PS_001 --source-kind public
```

`--from` 포함, `--to` 미포함입니다. 기간은 보고서 시간대의 날짜이며 기본 UTC입니다. `SOLAROPS_REPORT_TIMEZONE=Asia/Seoul`처럼 명시적으로 변경할 수 있습니다. 브라질 자료를 임의로 한국 시각으로 해석하지 않습니다.

51개 전체 처리: `uv run python scripts/data/full_dataset.py`. PostgreSQL/MinIO 전체 처리: `uv run python scripts/data/full_dataset.py --services`. 이미 다운로드한 파일의 checksum이 다르면 덮어쓰지 않습니다. 수정한 입력은 새 `--source-version`을 지정해야 합니다.

Airflow와 같은 제한을 사용하는 재처리 명령:

```bash
uv run solarops replay --source-kind public --plant PS_001 \
  --from 2024-04-03 --to 2024-04-04 --source-version brpvgen-v1
```

기본은 계획 확인이며 `--dry-run false`를 붙이면 실행합니다. 최대 31일, `--to` 미포함이며 경로·발전소·입력 범위를 먼저 확인합니다. Compose의 읽기 전용 원본 마운트, kind의 파일 복사, Airflow Params 예시는 [DAG 운영 안내](../runbooks/dags.md)에 있습니다.

## Kubernetes

Compose와 별도 DB/MinIO를 갖는 로컬 kind 클러스터입니다. 작은 메모리 환경에서는 Compose를 중지하고 진행하세요.

```bash
bash scripts/ops/install-k8s-tools.sh
make k8s-bootstrap
make k8s-deploy
make k8s-smoke
export KUBECONFIG="$PWD/artifacts/kubeconfig"
kubectl get pods -n solarops
```

kind 0.33.0, Kubernetes 1.35.0, Helm 3.19.0, Airflow chart 1.22.0, Airflow 3.3.2, KPO provider 10.24.0을 사용합니다. CLI 실행 Pod는 root 권한 없이 실행되며 CPU/RAM 한도가 있습니다. 스케줄러 LocalExecutor와 KubernetesPodOperator의 역할이 분리되어 있습니다.

도구 경로는 `.tools/kind`, `.tools/linux-amd64/helm` 또는 PATH를 사용합니다. Kubeconfig는 이 프로젝트의 `artifacts/kubeconfig`에 보관합니다. 클러스터·볼륨 삭제 명령은 자동 실행하지 않습니다.


## 환경 변수

CLI는 `.env`를 자동으로 읽지 않습니다. `.env.example`은 설정 안내이며 Compose는 명령의 `--env-file .env`로 읽습니다. 네이티브 CLI 설정은 셸에서 export해야 합니다.

```powershell
$env:SOLAROPS_DATA_DIR = "data/native-demo"
$env:SOLAROPS_REPORT_TIMEZONE = "UTC"
uv run solarops demo
```

```bash
export SOLAROPS_DATA_DIR=data/linux-native
export SOLAROPS_REPORT_TIMEZONE=UTC
uv run solarops demo
```

WSL에서 Make 없이 `uv run`을 직접 쓴다면 `export UV_PROJECT_ENVIRONMENT=.venv-linux`도 설정합니다. Bash의 여러 줄 명령은 PowerShell에 그대로 붙여넣지 말고 한 줄로 합칩니다. 기존 서비스 환경 변수가 설정되어 있다면 독립 데모 `scripts/demo/portfolio_demo.py`가 SQLite와 로컬 파일 경로를 명시하므로 안전하게 분리된 결과를 만듭니다.

| 설정 | 기본 / 용도 |
|---|---|
| `SOLAROPS_DATA_DIR` | `data`; 원본 사본, 임시 처리, 보고서 및 기본 SQLite |
| `SOLAROPS_DATABASE_URL` | 미설정 시 위 폴더의 SQLite; 서비스는 PostgreSQL |
| `SOLAROPS_S3_ENDPOINT` | 미설정 시 로컬 파일; 서비스는 MinIO |
| `SOLAROPS_S3_ACCESS_KEY`, `SOLAROPS_S3_SECRET_KEY` | MinIO 인증; Git/로그에 포함하지 않음 |
| `SOLAROPS_S3_BUCKET` | `solarops-demo` |
| `SOLAROPS_ORG` | `demo`; 프로세스 단위 조직 범위 |
| `SOLAROPS_REPORT_TIMEZONE` | `UTC`; 보고서의 일자 경계 |
| `SOLAROPS_SOURCE_DIR` | `data/source`; replay 입력 루트 |
| `SOLAROPS_SOURCE_HOST_DIR` | Compose에서 호스트 원본 마운트를 바꿀 때만 지정 |

서비스 연결 검사는 `make test-services`, 일반 개발 검사는 [기여 안내](../../CONTRIBUTING.md)를 따릅니다. 실행별 증거와 현재 검증 범위는 [구현 상태](../IMPLEMENTATION_STATUS.md)에 연결합니다.
