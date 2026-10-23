## 종합

총점은 **92 / 100**입니다. 코드와 문서가 서로 일치하고, 실패 보존·재처리 동등성·격리 PostgreSQL/MinIO 계약을 이 세션에서 직접 재현했습니다. 확인된 결함은 작은 것 3건이며, 게시 무결성이나 보안 경계를 깨는 문제는 찾지 못했습니다.

대상: 커밋 `954a421af31c34d14be99f0354ab783e4d18dec7`, 앱 0.5.5, 구현 `cedf70216add558956001140c56b6931c40a1198`. `solarops` import 경로가 이 export의 `src`로 해석되는 것을 먼저 확인했습니다.

## 항목별 점수 (각 0~5)

| # | 영역 · 항목 | 점수 | 근거 요약 |
|---|---|---:|---|
| 1 | DE · 출처/단위/시간 계약 | 5 | `docs/data-contract.md`, `docs/data-sources.md`, `docs/ons-source-contract.md`가 MD5/SHA, W→kWh 산식, ONS MWmed·`ts_utc=null`을 명시. `normalize/parquet.py:67-89`의 시각 계약이 문서와 일치하고 `test_bad_timestamps`가 통과 |
| 2 | DE · 파싱·정규화·충돌 | 5 | DuckDB 외부 정렬과 2,048행 배치(`parquet.py:43-64`, `pipeline.py:49-72`), canonical 인버터 ID, 동일키 동일값/상이값 구분(`pipeline.py:84-94`), metadata 중복 헤더 거부, ZIP 안전 추출. 기상 요청밖 행 미검증은 계약에 명시 |
| 3 | DE · 품질 분모·unknown·0 | 4 | 원본 범위 교집합 분모, null과 유효 0 구분, 보간 불명 표시가 보고서/UI/CSV에서 일관. 다만 `warning_count`가 중복 이슈를 세지 않는 결함 재현(발견 1) |
| 4 | DE · 증분/정정/철회 | 4 | ONS ETag·날짜 hash·cursor 조건부 전환·withdrawn(`ons.py:248-342`), BR `SOURCE_RANGE_SHRINK`·`--restore`·버전 충돌. 인버터 단위 소실은 거부하지 않고 사후 조사만 가능한 점이 문서화된 한계 |
| 5 | DE · 계보·결과 동등성 | 4 | raw SHA→manifest→시계열 SHA→보고서 SHA→freshness 비교까지 연결. 데모에서 재처리 7일 hash 동일 재현. 논리 hash에 버전 라벨이 포함되는 사실이 문서에 없음(발견 2) |
| 6 | 신뢰성 · 원자 게시·실패 보존 | 5 | 객체 업로드 후 단일 트랜잭션 게시(`pipeline.py:454-502`), before/during commit 주입 테스트 통과, 2차 기록 실패가 원인을 덮지 않음. 데모와 격리 PG에서 재현 |
| 7 | 신뢰성 · 동시성·재시도 | 5 | 기대 run_id 조건부 교체, PG advisory lock, `claim` 기반 버전 등록, 보고서 역순 완료 차단, ONS cursor 충돌. SQLite/PG 양쪽 경쟁 테스트가 이 세션에서 통과 |
| 8 | 신뢰성 · 조직/경로/비밀 경계 | 5 | 모든 조회가 org 스코프, 산출물 경로/버킷 검증(`api/app.py:67-94`), 오류 코드 허용 목록과 sentinel 비노출 테스트, 관리 서버 loopback·Origin·토큰. 인증 부재는 범위로 명시 |
| 9 | 신뢰성 · 진단·복구 절차 | 4 | 읽기 전용 `inspect-runs`, `docs/runbooks/recovery.md`의 코드별 조치표, 복원 드릴 스크립트. 복원 드릴은 이 세션에서 실행하지 않아 문서 근거로만 확인 |
| 10 | 신뢰성 · 회귀 검사의 의미와 실제 실행 | 4 | 검사가 실제 경계(주입 실패, 경쟁, 비노출)를 겨냥. 79개 오프라인 + 13개 서비스 검사 통과. `warning_count`를 검증하는 검사는 없고 전체 suite 일부는 미실행 |
| 11 | 아키텍처 · 역할·공통 CLI | 5 | `dags/solarops_factory.py`가 CLI만 호출하고 변환 로직 미복제, 모듈 책임이 `docs/architecture/system.md` 표와 일치 |
| 12 | 아키텍처 · 저장/조회 모델과 제약 | 4 | org/plant/day/tz/calc 버전 키의 active 포인터, 읽기 전용 Catalog, PG 표현식 인덱스, 단일 SELECT 조회 모델. `analyze` CLI가 쓰기용 Catalog로 DDL을 실행(발견 3), 마이그레이션은 create_all 기준선만 존재 |
| 13 | 아키텍처 · 기술 선택·비용·대안 | 5 | `docs/architecture/technology-stack.md`가 버전·역할·대안·재검토 조건을 표로 제시. Kafka/Spark 미채택 이유 명시 |
| 14 | 아키텍처 · 배포 버전·설정과 운영 경계 | 5 | `release.json` 단일 명세와 `release.py check` 통과, Dockerfile digest 고정, Helm/Compose 태그 정렬, Pod 보안 컨텍스트·SA 토큰 미장착 |
| 15 | 재현성 · 새 환경의 작은 오프라인 시연 | 5 | `portfolio_demo.py`가 새 폴더에서 정상→실패 주입→보존→재처리→보고서를 수행하고 통과. CI에서도 동일 실행 |
| 16 | 재현성 · 의존성·실행 버전/이미지 추적 | 5 | `uv.lock` 고정, 기반 이미지 digest, `docs/image-versions.json`, `docs/releases/0.5.5.json`, Airflow constraints SHA |
| 17 | 재현성 · 측정 절차·원본 요약·재현 한계 | 4 | 벤치마크마다 조건·한계가 명시되고 bounds 재현 코드 제공. 원본 측정 산출물은 Git 제외라 export만으로 수치 재현 불가 |
| 18 | 전달력 · README 동선 | 5 | 요약→5분 실행→데이터 의미→설계→근거→범위 순서. 제외 문서 링크는 export 범위 때문이며 결함 아님 |
| 19 | 전달력 · 주장과 코드/근거 연결 | 4 | `CASE_STUDY.md`, `DESIGN_QUESTIONS.md`가 코드·테스트·벤치마크로 연결. 논리 hash 설명이 버전 라벨 포함 사실을 생략 |
| 20 | 전달력 · 현재/과거/미완료 구분 | 5 | README 표, `IMPLEMENTATION_STATUS.md`, 벤치마크가 "역사 근거"와 최신 검증을 구분하고 미실행 항목을 명시 |

영역 합계는 데이터 엔지니어링 22, 신뢰성 23, 아키텍처 19, 재현성 14, 전달력 14입니다.

**근거가 확인된 강점**
- **실패 보존이 실제로 동작합니다.** 데모에서 커밋 중 주입 실패 뒤 7개 active hash가 그대로였고, 재처리 hash가 동일했습니다. 격리 PG에서도 같은 계약 7종이 통과했습니다.
- **오류 정보가 새지 않습니다.** `contracts/brpvgen.py:46-64`와 `acquisition/ons.py:75-91`이 허용 코드만 저장하고, `tests/test_pipeline.py:88-141`이 sentinel 값의 DB/파일/CLI 비노출을 검사합니다.
- **원본 캡처가 경합에 안전합니다.** `storage/minio.py:42-73`의 staging→fsync→SHA→hard link 순서와 `test_raw_copy_is_published_only_when_complete`가 통과했습니다.
- **조회는 저장소를 만들지 않습니다.** `Catalog(read_only=True)`와 `ObjectStore(initialize=False)`, `/ready` 503 검사가 통과했습니다.
- **ONS 계약이 보수적입니다.** 시간대 미명시를 그대로 보존하고 에너지에 합산하지 않으며, 정정·철회·충돌이 작은 fixture와 PG에서 검증됩니다.

**발견 사항과 최소 개선안**

1. **`warning_count`가 중복 이슈를 누락합니다. (재현됨, 영향 낮음)** `analytics/metrics.py:150`이 `warning_count`를 계산한 뒤 `pipeline.py:383-391`이 `DQ-DUPLICATE-IDENTICAL`을 추가합니다. 데모 `metrics.csv`의 2024-04-01은 `warning_count=0`인데 같은 날짜 manifest `issues`에는 중복 이슈 1건이 있습니다. HTML은 이 필드를 쓰지 않지만 CSV와 `/metrics` API에 노출됩니다. 최소 수정: `docs/data-contract.md`에 "`warning_count`는 분석기 규칙(누락·보간·무효)만 센다"고 한 줄 명시. 코드 수정(`pipeline.py`에서 hash 계산 전 `metric["warning_count"]=len(quality)`)은 중복이 있는 날짜의 논리 hash를 바꾸므로 계약상 계산 버전 승격과 함께 해야 합니다.

2. **논리 hash에 `dataset_version` 라벨이 포함됩니다. (정적, 문서 정확성)** `pipeline.py:392-393`이 metric에 `dataset_version=version`을 넣고 `pipeline.py:395-409`가 그 metric을 hash합니다. 같은 바이트를 새 `--source-version` 이름으로 재게시하면 hash가 달라지고 freshness가 `changed`가 됩니다. `docs/data-contract.md:29`, `docs/architecture/system.md:108`, `docs/portfolio/CASE_STUDY.md:48`, `docs/portfolio/DESIGN_QUESTIONS.md:7`은 run_id·시각만 제외된다고 설명하므로, `docs/runbooks/recovery.md:11`의 "이전/이후 논리 해시 비교" 절차에서 라벨 변경만으로 불일치가 날 수 있습니다. 최소 수정: data-contract에 "hash 동등성은 같은 source_version 라벨 안에서만 기대한다"는 한 문장 추가. 라벨 제외는 기존 hash를 바꾸므로 권하지 않습니다.

3. **`analyze` CLI가 읽기 조회에 쓰기용 Catalog를 씁니다. (정적, 영향 낮음)** `cli.py:259`는 `Catalog(settings)`로 `create_all`을 실행하므로 SQLite 경로가 없으면 빈 DB 파일을 만듭니다. `ons-status`(`cli.py:193-197`)는 `read_only=True`를 씁니다. 최소 수정: `analyze`도 같은 패턴으로 통일하고 `dispose`. `tests/test_replay.py:154-168`은 DB가 이미 있어 영향이 없습니다.

## 실행한 검사와 검토 범위·한계

실행 명령과 결과는 아래와 같습니다. 모두 이 export 디렉터리에서 실행했습니다.

| 명령 | 결과 |
|---|---|
| `python -c "import solarops; print(solarops.__file__)"` | `...\artifact-review-r4-20261023\source\src\solarops\__init__.py` |
| `pytest tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py` | 79 passed, 25.92초 |
| `scripts/demo/portfolio_demo.py --output artifacts/fable-r4-synthetic` | active 7, batch committed 2 · failed 1, `failed_publish_kept_active_data=true`, `replay_hashes_identical=true`, 보고서 `f1247dcb-...` `partial_period` |
| `scripts/release/release.py check` | `Release declarations aligned: 0.5.5` |
| `service-probe.py artifacts/fable-r4-services` | 13 passed, 21.16초. 컨테이너 `solarops-quality-pg-d1cba67c92`, `solarops-quality-s3-d1cba67c92` 중지·보존, 삭제 없음 |

데모 산출물의 `release.git_revision`은 대상 커밋과 같고 `source_dirty=null`이었습니다.

**검토한 경로**: `src/solarops/` 전체(pipeline, contracts, normalize, analytics, storage, acquisition, api, reports, diagnostics, replay, runtime, config, cli, admin, release.json, 템플릿), `tests/` 14개 파일, `dags/`, `infra/`(compose, Dockerfile 2종, helm values, k8s services), `.github/workflows/` 2종, `Makefile`, `pyproject.toml`, `migrations/0001_catalog.sql`, `scripts/`(demo, release, validation 주요 파일, ops bootstrap·k8s-secrets), `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `PRODUCT.md`, `docs/`(README, IMPLEMENTATION_STATUS, data-contract, data-sources, ons-source-contract, architecture 2종, ADR 0001~0008, guides 2종, runbooks 4종, benchmarks 주요 11종과 quality-v0.5.5.json, releases/0.5.5.json, image-versions.json, portfolio 4종, worklog/2026-10-23-bounds-reproduction.md, reviews/portfolio-rubric.md). 생성된 데모 `metrics.csv`와 `manifest.json`도 읽었습니다. `artifacts/astra-*`는 다른 평가자 산출물이므로 열지 않았습니다.

**한계**: 다음은 직접 실행하지 않았고 문서 기록으로만 확인했습니다. 전체 오프라인 suite 중 `test_admin`, `test_api_validation`, `test_packaging`, `test_replay`, `test_workspace`(단, `test_diagnostics`의 추적 검사는 서비스 검사 안에서 PG로 실행됨), SQLite/PG 복원 드릴, Airflow/kind DAG 실행, 브라우저 검사, 공개 51개 발전소 처리, 12,572 파티션 동등성, KPO 47.3% 단축, 동시 조회 p95 수치. 이들은 문서화된 과거 근거이며 이 세션의 통과로 기록하지 않습니다. 평가는 AI의 판단이며 외부 감사나 품질 보증을 대체하지 않습니다.