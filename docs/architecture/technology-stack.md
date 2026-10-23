# 기술 스택과 선택 근거

[문서 홈](../README.md) · [구조와 데이터 흐름](system.md)

설정된 기술과 실제 사용 증거는 [실행 스택·데이터 실사](../benchmarks/stack-authenticity-20261023.md)와 [v0.5.0 증분 수집·공개 DAG 측정](../benchmarks/incremental-v0.5.0.md)을 함께 확인합니다. 전체 BR-PVGen 처리는 Compose, kind의 기존 v2 결과는 공개 하루입니다. ONS 정기 수집은 kind의 독립 저장소를 사용하며 다른 6개 DAG는 중지 상태입니다(2026-10-23 확인).

BR-PVGen은 고정 배포 다운로드·역사 구간 재처리입니다. ONS는 실제 갱신되는 월별 CSV를 매일 조건부 HTTP GET하고 변경 날짜만 게시합니다. ETag·원본 SHA·성공 cursor·기대 run ID 비교로 재처리와 역순 게시를 제어합니다. 원문 MWmed와 시각을 보존하며 시간대가 미명시라 기존 추정 kWh에 합산하지 않습니다. [수집·일정·확장 절차](../guides/data-ingestion.md).

선택 기준은 로컬에서 재현 가능하고, 메모리 사용을 제한하며, 결과의 출처와 재시도 경계를 설명할 수 있는가입니다. 아래 버전은 직접 의존성 및 현재 인프라 설정 기준입니다. 전이 의존성은 [uv.lock](../../uv.lock), 현재 배포 커밋·이미지 식별자는 [v0.5.2 릴리스](../releases/0.5.2.json), 이전 이미지 목록은 [image-versions.json](../image-versions.json)을 확인합니다.

## 처리와 저장

MinIO는 공식 release tag를 지정한 자체 빌드입니다. 실행 바이너리의 `--version`은 `DEVELOPMENT.GOGET`으로 표시됩니다. 실제 S3 동작은 검증했지만 소스 아카이브 digest 고정·바이너리 재현 빌드까지 검증한 것은 아닙니다. Helm chart의 기본 app_version(3.2.2)과 실제 이미지의 Airflow(3.3.2)도 구별합니다.

| 기술 / 버전 | 담당 역할과 선택 근거 | 대안·비용·재검토 조건 |
|---|---|---|
| Python 3.12 / uv 0.11.29 | CLI·변환·분석·보고서·검사를 한 언어와 잠긴 의존성으로 실행. Windows/Ubuntu CI로 재현성 확인 | Python 행 처리는 CPU 비용이 있음. 대용량 정렬은 DuckDB에 위임. OS별 가상환경 분리 필요 |
| DuckDB 2.0.0 | CSV 필터와 외부 정렬. 512MB 메모리 한도·2스레드, 하루씩 Python에 전달 | 전체 CSV를 pandas 메모리에 올리는 경로보다 메모리 경계를 명시하기 쉬움. Spark의 분산 운영 비용은 이 단일 노드 작업에서 정당화되지 않았음. 두 대안과 직접 성능 비교한 것은 아님 |
| PyArrow 26.0.0 / Parquet ZSTD | 명시 스키마, 열 형식 저장, 원본 추가 필드는 `raw_json` 보존 | CSV보다 타입과 압축에 유리하지만 소규모 일별 파일이 많아질 수 있음. 더 큰 데이터에서는 파일 크기·파티션 압축을 측정한 뒤 조정 |
| SQLAlchemy 2.1.6 / psycopg 3.3.6 | 동일 카탈로그 코드로 SQLite와 PostgreSQL 사용. 일별 활성 포인터 전환을 트랜잭션으로 묶음 | 두 DB의 동시성·JSON 특성이 같지는 않음. 실제 PostgreSQL 통합 검사가 별도로 필요 |
| SQLite / PostgreSQL 16.10 | SQLite는 설치 없는 독립 데모, PostgreSQL은 실제 서비스 카탈로그와 다중 작업 실행. SQLite 버전은 Python 배포판에 따름 | SQLite는 운영 DB 대체물이 아님. JSON payload 확장은 쉽지만 장기 이력 조회 비용이 증가할 수 있어 측정 후 정규 컬럼·인덱스 추가 |
| MinIO / boto3 1.43.117 | S3 API로 원본·Parquet·시계열·보고서를 보관. 로컬 파일 ObjectStore와 동일한 업로드 경로 | 파일 저장소는 더 간단하나 서비스/Pod 공유 검증에 부족. 실제 AWS S3·IAM·수명주기 정책은 미검증. MinIO는 AGPLv3 |
| tzdata 2026.2 / pytz 2026.5 | UTC 입력과 보고서 현지 날짜 경계. zoneinfo와 Arrow 시간대 지원 | OS 시간대 데이터 차이를 줄이지만 DST 경계 회귀 검사가 필요. 시각대 없는 입력을 임의 추측하지 않음 |

MinIO는 공식 소스 `RELEASE.2025-10-15T17-29-55Z`를 [Dockerfile](../../infra/docker/Dockerfile.minio)로 빌드합니다. 이 환경에서 공식 공개 이미지/바이너리에 접근할 수 없어 선택한 방식이며, 소스 빌드 시간·업스트림 공급망·라이선스 검토 부담이 있습니다.

선택의 실측 근거는 [공개 전체 실행](../benchmarks/2026-10-22.md)입니다. 14,400,480행 처리의 native peak 714MiB는 DuckDB 한도 외 Python·Arrow 사용량을 포함합니다. 512MB를 전체 프로세스 메모리 보장으로 제시하지 않습니다.

실측에 따른 보완: 25,424개 실행 이력에서 발전소 필터가 전체 JSON을 읽는 병목을 확인했습니다. PostgreSQL의 조직·발전소 표현식 인덱스1개(200KiB)로 해당 조회 중앙값393→15ms를 확인했고, SQLite와 기존 JSON 저장 계약은 유지했습니다. 전체 이력의 장기 성능 보장은 아닙니다. [측정 조건·전후 실행계획](../worklog/2026-10-23-usability.md#perf-02-17점).

## 서비스와 실행 환경

| 기술 / 버전 | 담당 역할과 선택 근거 | 대안·비용·재검토 조건 |
|---|---|---|
| FastAPI 0.159.1 / Uvicorn 0.54.0 | 읽기 API, 경로·쿼리 검증, OpenAPI 및 정적 UI를 한 프로세스로 제공 | 별도 API Gateway·인증 서버 없음. 외부 운영 시 인증·HTTPS·권한 설계 필요 |
| HTML / CSS / JavaScript | 작은 읽기 중심 UI. 서버가 정적 자산을 제공하므로 브라우저 빌드·배포 단계 없이 wheel에 포함 | React/TypeScript의 컴포넌트·정적 타입 이점은 현재 포기. 화면과 팀 규모가 커지면 재검토. Node는 CI 문법 검사용이며 제품 실행 의존성이 아님 |
| Jinja2 3.1.6 | 원본 계보를 포함한 독립 HTML 보고서, 자동 이스케이프 | 브라우저 JavaScript 없이 공유 가능한 결과. PDF 자동 생성·서명은 미구현 |
| Docker / Compose | DB·객체 저장소·Airflow를 로컬에 재현. 앱 DB와 Airflow 메타 DB를 분리 | 데모 자체에는 불필요. 자원 사용·첫 이미지 빌드 시간이 증가하며 Docker Desktop 버전은 호스트 설치에 따름 |
| Airflow 3.3.2 / LocalExecutor | 의존성·실행 이력·재시도·수동 백필. DAG는 공통 CLI만 호출 | cron은 더 단순하지만 태스크 재시도·관찰 기능을 직접 구현해야 함. 이력 규모 대비 Airflow 운영 비용도 있음 |
| KPO provider 10.24.0 | KubernetesPodOperator가 작업별 CLI Pod를 생성, CPU/RAM·권한 격리 | LocalExecutor와 대체 관계가 아님. 스케줄러는 LocalExecutor, 실제 작업은 KPO Pod. 작은 작업의 Pod 기동 비용이 큼 |
| kind 0.33.0 / Kubernetes 1.35.0 / Helm 3.19.0 / Airflow chart 1.22.0 | 로컬에서 실제 Pod·서비스 DNS·PVC·롤아웃·중단 재시도를 검증 | 단일 노드 kind는 고가용성/재해복구 증거가 아님. 관리형 클라우드 운영·대규모 확장성 미검증 |
| pytest 9.1.1 / Ruff 0.17.1 / GitHub Actions | 실패 보존·중복 충돌·조직 격리·API·패키징 회귀, 두 OS에서 동일 검사 | 오프라인 CI에는 외부 서비스·전체 공개 자료가 없음. 실제 PostgreSQL/MinIO는 별도 선택형 self-hosted CI로 검증하며 실행기·서비스가 필요 |
| hatchling 1.29.0 | CLI와 템플릿·정적 파일을 wheel로 배포 | wheel 성공만으로 서비스 배포 완료를 뜻하지 않으므로 컨테이너/API 확인을 별도 기록 |

개발 의존성의 httpx2 2.16.0은 FastAPI TestClient, psutil 7.2.2는 실제 메모리/실행 측정에 씁니다. Airflow 환경은 자체 의존성 제약이 있으므로 [별도 venv를 복사하는 이미지](../../infra/docker/Dockerfile)로 앱 환경과 분리합니다. 앱은 uv.lock에 잠겨 있지만 Airflow 이미지의 전이 의존성 전체가 같은 lockfile로 잠긴 것은 아닙니다. 이미지 digest를 검증 기록에 남깁니다.

## 사용하지 않은 기술의 판단

### 로컬 시스템 관리의 분리

관리 UI는 같은 FastAPI·정적 HTML/CSS/JS를 재사용하되 호스트의 `solarops admin`(8504)으로 분리했습니다. 분석 대시보드(8502)를 중지해도 관리가 가능해야 하며, 웹 컨테이너에 Docker 소켓을 마운트하지 않기 위한 선택입니다. 임의 명령 대신 고정 허용 목록과 소속 라벨/Compose 경로 확인 후 subprocess 인수로 기존 컨테이너만 시작·중지합니다.

Host·loopback·Origin·CSRF·한 번에 한 작업·시간 제한·조작 기록을 적용합니다. 이는 이 PC의 로컬 도구 범위이며 사용자 인증·원격 권한 모델을 대체하지 않습니다. 컨테이너 삭제, SQL, Docker 엔진 중지, 외부 배포는 기능에 넣지 않았습니다. [조작 범위](../runbooks/operator.md#시스템-관리-8504), [실제 수명주기 검증](../benchmarks/workspace-20261023.md).

실시간 입력 요구가 없어 Kafka/스트리밍 시스템을 추가하지 않았습니다. 확인된 고장 정답 라벨이 없어 ML 정확도를 주장하지 않으며 설명 가능한 검토 후보 규칙을 사용합니다. 다수 사용자 수정 흐름이 없어 프런트엔드 상태 관리 서버도 없습니다. 이 선택은 실제 요구가 바뀌면 다시 검토할 대상입니다.

평가자는 도구 개수보다 [입력 계약](../data-contract.md), [실패·복구 경계](../runbooks/recovery.md), [같은 CLI의 환경별 실행](../runbooks/dags.md), [성능 주장의 조건](../benchmarks/workspace-v0.3.0.md)을 코드와 연결해 확인할 수 있습니다.
