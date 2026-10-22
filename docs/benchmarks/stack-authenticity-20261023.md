# 기술스택 실사용과 데이터 출처 점검

2026-10-23 Asia/Seoul, 코드 `4e6d1d2`와 실행 중인 로컬 서비스를 읽기 전용으로 점검했습니다. **제품은 실제 Python·DB·객체 저장소·작업 오케스트레이션으로 구현되어 있습니다. 공개 자료 화면은 BR-PVGen에서 계산한 값이며, 합성 시험 데이터도 별도로 존재합니다.**

[검사 결과 JSON](evidence/stack-authenticity-20261023.json) · [원본 출처](../data-sources.md) · [기술 선택 근거](../architecture/technology-stack.md) · [수행 기록](../worklog/2026-10-23-authenticity.md)

## 무엇을 직접 확인했는가

| 기술 | 실제 사용 증거 | 현재 상태와 범위 |
|---|---|---|
| Python 3.12.13 · FastAPI 0.159.1 · Uvicorn 0.54.0 | 실행 중인 dashboard 컨테이너의 Python/패키지 버전, `/ready`, 읽기 API, 배포 소스 36개 해시와 저장소 일치 | Compose의 8502 서비스를 사용. React·Next.js 앱이 아니라 HTML/CSS/JavaScript |
| SQLAlchemy 2.1.6 · psycopg 3.3.6 · PostgreSQL 16.10 | 실제 연결 dialect와 `SELECT version()`, 활성 파티션·지표·실행 이력을 직접 조회 | 공개 v2 파티션 12,572개. 화면에 고정된 수치를 넣는 코드가 아니라 DB 조회 결과 |
| DuckDB 2.0.0 · PyArrow 26.0.0 · Parquet | 배포 처리 코드가 CSV를 DuckDB로 필터·정렬하고 Arrow로 저장. MinIO의 실제 ZSTD Parquet를 Arrow로 읽고 DuckDB 집계와 독립 CSV 계산 대조 | 대표 인버터 3,744행·기상 96행의 원본 필드·값·유효/보간·표본 수 일치 |
| MinIO · boto3 1.43.117 | 실제 S3 GET으로 raw·Parquet·보고서를 읽고 해시 확인. HTTP 보고서와 객체 바이트 일치 | 실행 중. 자체 빌드 바이너리는 `DEVELOPMENT.GOGET` 표시이며 아래 한계 참조 |
| Jinja2 3.1.6 | 배포 `render.py`가 DB 스냅샷으로 템플릿을 렌더. 저장된 HTML·CSV·manifest의 SHA-256 및 HTTP 반환 바이트 확인 | 이번 점검에서는 보고서를 재발행하지 않고 기존 산출물을 확인 |
| Docker · Compose | dashboard/app-db/minio 실제 컨테이너와 프로세스·저장소 연결 | 기본 3개 실행 중, Compose Airflow 4개는 중지 상태 |
| Kubernetes 1.35.0 · kind 0.33.0 | 실제 노드 Ready, namespace `solarops`의 Pod 상태·종료 코드·이미지 및 KPO 로그 조회 | 실행 서비스 Pod 6개 모두 Ready, 보존된 Succeeded 95개·Failed 3개. 단일 로컬 노드 |
| Airflow 3.3.2 · KPO provider 10.24.0 | Airflow 메타DB의 DAG 실행 44개·태스크 80개 성공, operator가 실제 `KubernetesPodOperator`. 최근 공개 5개 시나리오의 9개 태스크와 exit 0 Pod 대응 확인 | kind 안에서 LocalExecutor 사용. DAG 4개 모두 paused이며 자동 수집은 하지 않음 |
| Helm 3.19.0 · chart 1.22.0 | CLI 버전, 실제 release revision 10의 `deployed`, workload의 Helm 라벨 | chart 기본 app_version은 3.2.2지만 사용자 이미지의 실제 Airflow는 3.3.2. 둘을 같은 버전으로 보지 않음 |
| SQLite | 기존 로컬 카탈로그도 직접 읽어 과거 v1 공개 파티션 12,572개의 논리 해시·지표를 Compose v1과 대조 | 기본 `data/solarops.db`는 v1 보존본. 현재 8502의 PostgreSQL v2와 실행 경로가 다름 |

Airflow/Kubernetes는 대시보드 요청마다 실행되는 기술이 아닙니다. 입력 재처리·백필·품질 확인·보고서 발행을 맡고, 화면은 이미 발행된 결과를 조회합니다. Node는 개발 검사 도구이며 제품 서버가 아닙니다. [배포 구조](../architecture/system.md), [공통 CLI를 실행하는 DAG](../../dags/solarops_factory.py), [API](../../src/solarops/api/app.py), [화면 API 호출](../../src/solarops/api/static/dashboard.js).

## 공개 데이터와 합성 데이터

| 데이터 | 현재 저장·조회 증거 | 해석 |
|---|---|---|
| 공개 `public` | 전체 기간 51개 발전소·인버터 14,400,480행·현재 계산 v2 파티션 12,572개 | 외부 제작자가 공개한 역사 자료. SolarOps가 임의로 만든 발전소 수치가 아님 |
| 공개 2024년 4월 | 5개 발전소·140개 파티션, 추정 에너지 1,477,828.846 kWh | 유효 161,084 / 무효 34,180 / 누락 0. 원본 보간 19,318은 별도 속성 |
| 합성 `synthetic` | DEMO_01·7개 파티션·정규화 인버터 1,342행, 추정 에너지 832.424 kWh | [생성기](../../src/solarops/fixtures.py)가 만든 명시적 시험 자료. 누락 2·보간 2·검토 후보 1을 시험 |
| 실패 기록 | Compose 앱 DB의 실패 14개 모두 `INJECTED_DURING_COMMIT` | 의도적인 커밋 실패 시험이며 실제 현장 사고가 아님 |

화면 기본값 `source=public`은 공개 자료만 선택합니다. `synthetic`은 시험 데이터, `all`은 둘을 합친 조회입니다. `source_kind` 표시는 입력 메타데이터이므로 그것만으로 외부 원본의 진위를 보증하지 않습니다. 이번에는 표시 외에 파일 해시·계보·계산을 아래와 같이 대조했습니다.

### 외부 원본과 파일 동일성

1. [Zenodo API](https://zenodo.org/api/records/21511487)를 새로 조회했습니다. 원본 ZIP을 다시 다운로드하지 않았습니다.
2. 로컬 원본 4개 모두 게시된 MD5·파일 크기와 일치하고, 보존 manifest의 SHA-256도 일치했습니다.
3. 인버터/기상 ZIP 안의 CSV 102개를 스트리밍 해시로 읽어 기존 압축 해제 파일 102개와 일치함을 확인했습니다.
4. 현재 공개 파티션들이 참조하는 고유 source object 103개(메타데이터 1·CSV 102)의 SHA-256을 이 파일들과 모두 대조했습니다.
5. 대표 PS_001의 MinIO raw 3개는 객체 전체를 직접 읽어 SHA-256 일치를 확인했습니다. **103개 S3 raw 객체 모두를 다시 읽은 것은 아닙니다.**

게시자가 제공한 해시는 MD5이고 SolarOps의 보존·계보 해시는 SHA-256입니다. 이 검사는 파일이 게시된 자료와 같은지를 확인합니다. 제작자의 현장 계측 정확성을 독립 검증한 것은 아닙니다.

### 하나의 수치를 끝까지 추적

대상: `PS_001 / 2024-04-03 / UTC / energy-interval-v2`.

| 대조 단계 | 확인 결과 |
|---|---|
| raw CSV → Parquet | 인버터 3,744행·기상 96행의 전체 필드 대조. CSV 빈 셀은 DuckDB의 `null` 표현으로 비교 |
| 원본 독립 계산 | 제품 `analyze()`를 호출하지 않고 CSV의 유한한 0 이상 W값 2,751개를 `math.fsum(W) / 1000 × 0.25`로 합산 |
| Parquet SQL → PostgreSQL → API | **19,752.692125 kWh** 모두 일치, 무효 993개 |
| 월간 CSV·manifest | 해당 날짜 값 일치. PS_001 4월 합계 **585,980.279 kWh**, 공개 source_kind만 포함 |
| 보고서 객체 → HTTP | HTML·CSV·manifest 3개 모두 등록 SHA-256 및 반환 바이트 일치 |
| kind 작업 로그·별도 앱 DB | 같은 하루의 추정 에너지와 논리 해시가 Compose와 일치 |

논리 해시: `564c16574fd94d1609fc62d05cbec262ebec50f5a2a5731a971745a0232bcdfb`.
Compose 파티션 실행: `40bef888-1cbb-45f9-b822-79fee15c9110`.
검사 보고서: `d9a964f0-8846-4785-8989-9d392c7927a3`.

추가로 v1 native/Compose 전체 12,572개 공개 파티션의 논리 해시·지표가 동일함을 재확인했습니다. Compose의 v1/v2 전체 일별 지표도 계산 버전 필드 외에 동일합니다. **현재 native v2는 0개**이며, v2 전체를 native에 처리했다는 주장은 하지 않습니다. [기존 v2 이관 범위](reliability-v0.4.0.md).

## 실제 작업 이력과 현재 상태

최근 공개 시나리오는 `k8s-public-{plan,normal,backfill,quality,report}-1792682448`입니다. Airflow 메타DB의 성공 기록과 Pod 라벨·종료 코드 0을 대응시켰습니다. normal Pod `solarops-replay-validate-publish-r11m0yth`의 보존 로그에 3,744행·같은 논리 해시·추정 에너지가 기록되어 있습니다. 이번 점검에서 과거 작업을 새로 실행한 것은 아닙니다.

보존된 Failed Pod 3개는 이전 장애/재시도 시험에 대응하며, Airflow에서 해당 태스크가 try_number=2에 성공한 것을 확인했습니다. 과거 실패 Pod가 남아 있는 것과 현재 서비스가 고장 난 것은 다릅니다. DAG를 재개하거나 서비스를 켜고 끄지는 않았습니다.

kind 앱 DB는 Compose와 별도입니다. 현재 kind v2에는 공개 하루 **1개 파티션**만 있고, v1 시험 파티션 8개는 보존되어 있습니다. 전체 51개 공개 자료 처리 실적은 Compose/네이티브의 해당 검증 범위이며, 전체 데이터를 Kubernetes에서 처리했다고 표현하면 안 됩니다.

## 남는 한계와 정확한 포트폴리오 표현

- BR-PVGen은 원본 제작자가 집계·일부 보간한 역사 자료입니다. 현재 고객 설비에 연결된 실시간 서비스는 아닙니다.
- 에너지는 유효 전력으로 계산한 추정치입니다. 계량기 실측 전력량·매출·확정 손실·현장 고장 정답을 검증하지 않았습니다.
- MinIO의 실제 S3 동작은 확인했습니다. [빌드 파일](../../infra/docker/Dockerfile.minio)은 공식 release tag를 지정하지만 바이너리 버전은 `DEVELOPMENT.GOGET`입니다. 이번에 원격 소스와 바이너리의 재현 빌드까지 검증하지 않았고, 소스 아카이브 digest 고정도 현재 빌드 파일에는 없습니다.
- 수작업 재처리·합성 장애 시험·단일 노드 kind 검증은 운영 활용 증거이며 고객 운영 실적·고가용성·대규모 확장성 증거와 구별해야 합니다.

이력서에는 **“공개 태양광 데이터 51개 발전소·1,440만 인버터 관측을 처리하고 PostgreSQL/MinIO 기반 보고서를 구현했다. Airflow/KubernetesPodOperator로 제한된 공개 자료 재처리와 합성 장애·재시도를 검증했다”**고 기술할 수 있습니다. 실시간 고객 운영·실측 발전량·전체 자료 Kubernetes 처리라는 표현은 현재 증거를 넘습니다.

## 점검 명령과 근거 보존

실행 명령은 `docker ps -a`, `docker exec -i solarops-audit-dashboard-1 python -`, `wsl -e kubectl --context kind-solarops ...`, `helm list -n solarops`, `airflow version` 및 읽기 전용 SQL입니다. Python 보조 스크립트로 Zenodo 메타데이터·기존 파일 해시·독립 CSV 계산·카탈로그 비교를 수행했습니다. 앱 DB는 `Catalog(..., read_only=True)`, Airflow DB는 PostgreSQL read-only connection, kind 앱 DB는 `BEGIN READ ONLY`로 조회했습니다.

실행 스크립트와 상세 JSON·Pod 목록·작업 로그는 로컬 `artifacts/stack-authenticity-20261023/`에 보존했습니다. Git에는 비밀·원본 행·접속 문자열을 제외한 [검사 결과 요약 JSON](evidence/stack-authenticity-20261023.json)을 포함합니다. 앱 코드·계산·데이터를 변경하지 않았으므로 전체 데이터 재처리·장애 주입·전체 회귀 시험은 새로 수행하지 않았습니다.
