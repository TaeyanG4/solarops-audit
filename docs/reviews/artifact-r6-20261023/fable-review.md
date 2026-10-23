## SolarOps Audit 독립 산출물 평가 (R6, Fable)

대상 커밋 fc64c4d785729b934e43ff62b76688f6f60d4431, 앱 선언 0.5.6 + CHANGELOG Unreleased 2건. 검토 범위는 `artifacts/artifact-review-r6-20261023/source-fable` 내보내기(303개 추적 파일)만이며, 원본 저장소·다른 평가·handoff/plan/worklog는 읽지 않았습니다. 평가 기준은 `docs/reviews/portfolio-rubric.md` v1의 고정 20항목(각 0~5)입니다.

**총점: 91 / 100**

| 영역 | 세부 항목 | 점수 | 근거 요약 |
|---|---|---:|---|
| 데이터 엔지니어링 (24/25) | 출처/단위/시간 계약 | 5 | `docs/data-contract.md`·`data-sources.md`·`ons-source-contract.md`에 MD5/SHA-256·단위·시각 규칙 명시. `normalize/parquet.py:67-89` 시각 형식·tz·15분 그리드 검증이 `test_contracts.py`로 실행 확인 |
| | 파싱·정규화·충돌 | 5 | 인버터 ID 정규형, 값/보간/표본수 코드화된 오류, 동일키 상이값 `DUPLICATE_CONFLICT`(`pipeline.py:84-94`), `raw_json` 원본 보존. 테스트 통과 직접 확인 |
| | 품질 분모·unknown·0 | 4 | 분모=인버터별 관측범위∩요청일, 무효 전용 슬롯 null, 보간 불명 별도 집계. 단, overview 요약과 보고서의 불명 처리 불일치(발견 1) 재현 |
| | 증분/정정/철회 | 5 | ONS 월별 cursor·변경일만 게시·철회 manifest·`ONS_CURSOR_CONFLICT`(`acquisition/ons.py:248-342`), BR `SOURCE_RANGE_SHRINK`·`--restore`. SQLite·격리 PostgreSQL 양쪽 테스트 통과 |
| | 계보·결과 동등성 | 5 | 논리 해시에 정규화값·지표·규칙·시계열 포함, 원본 SHA·series/artifact SHA 조회 검증. 데모에서 실패 후 재처리 7일 해시 동일 직접 확인 |
| 신뢰성 (24/25) | 원자 게시·실패 보존 | 5 | 객체 선저장→DB 조건부 active 전환(`pipeline.py:454-502`), 실패 staging 보존. 데모·테스트·격리 PG에서 재현 |
| | 동시성·재시도 | 5 | PG advisory lock, run_id 조건부 UPDATE, `claim` INSERT-ON-CONFLICT, SQLite 경합 계측 테스트, Airflow retry 2회. 격리 PG 동시 claim 테스트 통과 |
| | 조직/경로/비밀 경계 | 5 | 모든 조회 org 조건, 경로 `is_relative_to` 검사, 오류 코드 허용목록·비밀 미출력(`contracts/brpvgen.py:47-65`), Compose/k8s 비밀은 env/secretKeyRef, 관리서버 loopback·Origin·토큰 |
| | 진단·복구 절차 | 4 | `inspect-runs` 읽기전용 진단, `recovery.md` 코드별 절차, SQLite 복원 drill 직접 통과. PG/MinIO·별도 인스턴스 복원은 역사 증거만 확인 |
| | 회귀 검사의 의미와 실제 실행 | 5 | 오프라인 141통과·14제외(제외는 서비스 opt-in 13·symlink 1), 격리 PG/MinIO 13통과. 실패 주입·경합·조직 격리 등 의미 있는 경계 검사 |
| 아키텍처 (18/20) | 역할·공통 CLI | 5 | 네이티브·Compose subprocess·KPO가 같은 `solarops` CLI 호출(`dags/solarops_factory.py`), DAG에 계산 미복제 |
| | 저장/조회 모델과 제약 | 4 | JSON payload 테이블·active 포인터 모델은 명확하나 제약은 PK/UNIQUE 위주, 조회는 Python 물질화 후 슬라이스(문서화된 한계), 보고서 `scope` 열의 selection 키 재사용 |
| | 기술 선택·비용·대안 | 5 | `technology-stack.md`가 버전·대안·비용·재검토 조건을 항목별로 기록, Kafka/Spark 미채택 이유 명시 |
| | 배포 버전·설정과 운영 경계 | 4 | 단일 `release.json`·`release.py check` 통과·digest 고정 Dockerfile·KPO 보안 컨텍스트. 이미지 목록이 두 파일로 분산(발견 4), 이번 커밋 변경은 미빌드(선언됨) |
| 재현성 (13/15) | 새 환경의 작은 오프라인 시연 | 5 | 새 .venv에서 `portfolio_demo.py` 성공: 실패 주입→보존→재처리 해시 동일→보고서 생성 |
| | 의존성·실행 버전/이미지 추적 | 4 | uv.lock·Dockerfile digest·Airflow constraints SHA·`releases/*.json`. Airflow 전이 의존성은 lock 밖, MinIO 자체 빌드 재현성 미검증(문서화됨) |
| | 측정 절차·원본 요약·재현 한계 | 4 | 벤치마크마다 조건·한계·JSON 요약·지연 표본 1,080건 포함. 성능·KPO 수치는 재현하지 않은 역사 증거 |
| 전달력 (12/15) | 처음 보는 사람의 README 동선 | 4 | 재현→데이터→설계→근거 순서와 경계 서술이 좋음. 문장당 수치 밀도가 높고 외부/제외 문서 링크가 많아 첫 독자의 부담이 큼 |
| | 주장과 코드/근거 연결 | 4 | 대부분의 주장에 코드·테스트·벤치마크 링크. CI 링크·"최초 MVP부터 기록" 같은 이력 주장은 산출물만으로 확인 불가 |
| | 현재 상태·과거 증거·미완료 구분 | 4 | 버전별 라벨링과 Unreleased 선언이 명확. `IMPLEMENTATION_STATUS.md:11`이 이번 커밋에서 완료한 항목을 아직 "계획 등록"으로 서술(발견 5) |

**근거가 확인된 강점**

- 게시 경계가 코드와 테스트로 일치합니다. `pipeline.py:177-213`에서 배치 시작 시 기대 active를 캡처하고, `pipeline.py:463-477`에서 run_id 조건부 교체로 늦은 배치를 거부합니다. `test_publication_boundaries.py`의 겹침·역순 보고서 검사가 SQLite와 격리 PostgreSQL 양쪽에서 통과했습니다.
- 불명을 0으로 바꾸지 않는 원칙이 계산·보고서·UI에 일관되게 구현되어 있습니다. `analytics/metrics.py:133`의 null 전력, `reports/render.py:49-50`의 `METRIC_CONTRACT_MISMATCH`(이번 커밋 신규), `monthly.html:11-16`과 `dashboard.js:74-80`의 "알 수 없음" 표시를 확인했습니다.
- 이번 커밋의 SQL baseline은 모델과 완전히 일치합니다. SQLAlchemy PostgreSQL dialect로 생성한 DDL 15문과 `migrations/0001_catalog.sql`을 정규화 비교한 결과 누락 0·초과 0입니다. 기존 테스트의 부분 문자열 검사보다 강한 확인입니다.
- ONS 수집기는 원문 시각/단위를 변환하지 않고 `ts_utc=null`을 유지하며, 실패 코드 허용목록으로 비밀을 노출하지 않습니다. 21회 연속 실패 뒤에도 cursor가 보존되는 검사가 통과했습니다.
- 데모 보고서 manifest의 `release.git_revision`이 대상 커밋 fc64c4d로 기록되어 실행 식별이 추적됩니다.

**발견 사항과 최소 개선안**

1. **overview 요약과 보고서의 보간 불명 처리 불일치 (재현).** 관측 192슬롯이 전부 보간 불명인 합성 하루에서 `/api/v1/overview` 요약 `source_interpolation_ratio`는 `0.0`, 같은 자료의 보고서 manifest `interpolation`은 `null`입니다. 원인은 `api/readmodels.py:45-47`이 observed만 보고 나누는 반면 `reports/render.py:107-112`는 `observed > unknown` 조건을 둡니다. 대시보드는 `dashboard.js:76`에서 불명 수로 "알 수 없음"을 복원하므로 화면 영향은 없지만, API만 읽는 소비자는 0%로 오독할 수 있습니다. 최소 개선: `finish()`에서 `observed <= interpolation_unknown_slots`이면 `None`을 반환하거나, `data-contract.md`의 CSV 필드 설명과 같은 문장을 overview 요약 필드에도 명시합니다.
2. **범위 밖 지표 행의 처리 방식이 읽기 경로마다 다름 (정적).** `readmodels.py:31`의 `metric.get(key, 0)`은 필수 필드가 없는 행을 0으로 합산하고, 같은 행을 보고서는 `METRIC_CONTRACT_MISMATCH`로 거부합니다. 모든 생성기가 필드를 기록한다는 전제가 맞으면 영향은 없으나 계약 서술("불명을 0으로 채우지 않음")과 overview 동작이 어긋납니다. 최소 개선: overview에서도 `REQUIRED_METRIC_FIELDS` 검사를 공유하고 위반 시 503으로 응답하거나, overview의 관용 동작을 계약 문서에 적시합니다.
3. **`report` 명령이 없는 SQLite 카탈로그를 생성 (정적, 실행 확인 못함).** `reports/render.py:44`가 쓰기용 `Catalog`를 열어 `storage/postgres.py:150-157`에서 스키마를 만든 뒤 `NO_ACTIVE_PARTITIONS`로 실패합니다. 0.5.6에서 `analyze`에 적용한 "없는 DB를 만들지 않는" 경계가 `report`에는 없습니다. 영향은 빈 DB 파일 1개로 작습니다. 최소 개선: snapshot은 읽기 전용 Catalog로 먼저 수행하고 발행 단계에서만 쓰기 Catalog를 엽니다.
4. **이미지 식별자 기록이 두 곳으로 분산 (정적).** `docs/image-versions.json`은 0.5.5까지만 있고 0.5.6 digest는 `docs/releases/0.5.6.json`에만 있습니다. `technology-stack.md:9`가 전자를 "이전 이미지 목록"이라고 설명해 모순은 아니지만 단일 조회 지점이 없습니다. 최소 개선: 0.5.6 두 항목을 추가하거나 JSON 상단에 현재 릴리스의 위치를 적습니다.
5. **상태 문서 한 문장이 이번 커밋보다 뒤처짐 (정적).** `IMPLEMENTATION_STATUS.md:11`은 지표 필드 계약과 SQL 문서 정합성을 "다음 계획에 등록"으로 적었으나 `CHANGELOG.md:3-6`은 같은 항목을 Unreleased 완료로 기록합니다. 최소 개선: 해당 문장을 완료 상태로 갱신합니다.

배포 이미지의 소스 커밋(4b9959e)과 대상 커밋(fc64c4d)이 다르고 이번 변경이 빌드되지 않은 점은 CHANGELOG에 선언되어 있어 결함이 아닌 한계로 분류했습니다. 제외된 handoff/plan/review/worklog로 가는 끊어진 링크도 포장 결함으로 보지 않았습니다.

**실행한 명령과 결과**

```text
uv sync --frozen --offline --python H:/dev/solarops_audit/.venv/Scripts/python.exe
  → 새 .venv 생성, 42개 패키지 설치, 오프라인 캐시로 충분(네트워크 재시도 불필요)
.venv/Scripts/python.exe -c "import solarops; print(solarops.__file__)"
  → ...\source-fable\src\solarops\__init__.py, __version__ 0.5.6
.venv/Scripts/python.exe -m pytest -q --tb=short --junitxml=artifacts/fable-tests.xml
  → 155 수집 / 141 passed / 14 skipped / 0 failed, 59.8초
     skipped: test_services 13건(SOLAROPS_TEST_SERVICES opt-in), test_source_symlink_cannot_escape_root 1건(호스트 symlink 불가)
.venv/Scripts/python.exe scripts/demo/portfolio_demo.py --output artifacts/fable-demo
  → failed_publish_kept_active_data true, replay_hashes_identical true, 7 파티션, committed 2·failed 1, 보고서 partial_period
.venv/Scripts/python.exe scripts/validation/backup_restore_drill.py --output artifacts/fable-restore
  → 34 파일 백업, integrity ok, 손상 사본 거부, 복원 API·보고서 바이트 일치, 재처리 해시 동일
.venv/Scripts/python.exe scripts/release/release.py check
  → Release declarations aligned: 0.5.6
.venv/Scripts/python.exe H:/.../service-probe.py artifacts/fable-services
  → 새 컨테이너 2개(postgres:16.10-bookworm, solarops-minio:2025-10-15-pinned), 13 passed / 0 skipped, 26.5초, 컨테이너 중지·보존·삭제 없음
python -c (SQL baseline 대조)
  → 생성 DDL 15문 중 누락 0, 파일 초과 0
python -c (보간 전부 불명 합성 하루, artifacts/fable-probe-unknown)
  → overview ratio 0.0 / unknown 192 / observed 192, report interpolation None / unknown 192
```

실행하지 못한 검사: `ruff check`, `ruff format --check`, `scripts/validation/check_docs.py`, `report` 명령의 빈 DB 생성 재현 probe. 네 건 모두 이 세션의 도구 권한에서 거부되어 실행 결과가 없습니다. Ruff·문서 링크 통과는 CI 기록상의 주장이며 제가 확인한 것이 아닙니다.

**검토한 경로**

- 루트: `AGENTS.md`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `PRODUCT.md`, `Makefile`, `pyproject.toml`, `.env.example`, `.gitattributes`, `REVIEW_SNAPSHOT.json`
- 소스 전체 `src/solarops/**` (pipeline, analytics, normalize, contracts, storage, acquisition, reports, api, admin, diagnostics, replay, runtime, config, fixtures, release.json, dashboard.js 일부, monthly.html 일부)
- 테스트 전체 `tests/**`, `migrations/0001_catalog.sql`
- 인프라: `infra/compose/compose.yaml`, `infra/docker/Dockerfile`, `infra/k8s/services.yaml`, `infra/helm/airflow-values.yaml`, `dags/solarops_factory.py`, `dags/solarops_ons_daily.py`, `.github/workflows/ci.yaml`, `.github/workflows/services.yaml`
- 스크립트: `scripts/README.md`, `release/release.py`, `demo/portfolio_demo.py`, `validation/backup_restore_drill.py`, `validation/service-test.py`, `ops/bootstrap.py`, `ops/k8s-secrets.py`
- 문서: `docs/README.md`, `data-contract.md`, `data-sources.md`, `ons-source-contract.md`, `IMPLEMENTATION_STATUS.md`, `image-versions.json`, `architecture/system.md`, `architecture/technology-stack.md`, `adr/0002,0003,0004,0007,0008`, `guides/setup.md`, `guides/data-ingestion.md`, `runbooks/recovery.md`, `runbooks/backup-restore.md`, `runbooks/dags.md`, `runbooks/operator.md`(일부), `portfolio/SUBMISSION.md`, `DEMO_GUIDE.md`, `CASE_STUDY.md`, `benchmarks/quality-v0.5.6.md/.json`, `incremental-v0.5.0.md`, `technical-20261023.md`, `stack-authenticity-20261023.md`, `portfolio-finish-20261023.md`(일부), `evidence/technical-20261023/README.md`, `releases/0.5.6.json`, `portfolio/images/workspace-20261023/overview.png`
- 추가 읽기 예외: `H:/dev/solarops_audit/artifacts/artifact-review-r6-20261023/service-probe.py` (실행 전 검토)
- 제가 기록한 산출물: `artifacts/fable-tests.xml`, `artifacts/fable-demo/`, `artifacts/fable-restore/`, `artifacts/fable-services/`, `artifacts/fable-probe-unknown/`, pytest 임시 `artifacts/test-tmp/`

**한계**

- 직접 실행한 것은 오프라인 테스트, 합성 데모, SQLite 복원 drill, 릴리스 선언 검사, 격리 PostgreSQL/MinIO 13검사, 소규모 합성 probe 2건입니다. 공개 51개 발전소 처리, Airflow/KPO 실행, kind 배포, 성능 측정, PG/MinIO 복원 drill, Agent Browser 화면 검증은 문서상 역사 증거로만 평가했습니다.
- 내보내기에 `.git`이 없어 `release_info()`의 커밋 식별은 실행기가 설정한 `SOLAROPS_BUILD_REVISION`에 의존합니다. "최초 MVP 커밋부터 필드 기록" 같은 이력 주장은 확인 불가입니다.
- 외부 링크(GitHub Actions, Zenodo, ONS)와 비공개 저장소 접근은 시도하지 않았습니다.
- 점수는 AI 판단이며 외부 감사·품질 보증을 대체하지 않습니다. 확인된 중요 결함이나 필수 검사 실패는 없었습니다. 발견 5건은 모두 낮은 영향의 계약 일관성·문서 정합 문제입니다.