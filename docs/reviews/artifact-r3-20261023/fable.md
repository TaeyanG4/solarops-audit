## 독립 산출물 평가 (Fable R3)

**검토 조건.** 평가자 Claude Fable 5.1(claude-fable-5-1), Claude Code 세션. 대상 커밋 `36ac6ff937b06a481988d9264c65ac1a9597a59a`(`git rev-parse HEAD`로 확인), 앱 0.5.4 / 구현 93ad341, 계산 `energy-interval-v2`. 기준은 `docs/reviews/portfolio-rubric.md` v1의 20개 세부 항목(각 0~5점, 총 100점)이며 면접·개인 역량·채용 판단은 하지 않았습니다. 이전 점수·목표 점수·다른 평가자 결과는 보지 않았습니다.

### 실행한 검사와 결과

| 명령 | 결과 | 비고 |
|---|---|---|
| `git rev-parse HEAD` | `36ac6ff…` | 대상 커밋 일치 |
| `pytest tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py -q --basetemp artifacts/fable-r3-pytest-20261023` | **79 passed, 0 failed, 0 skipped, 24.50초** | SQLite·로컬 파일 경로. 서비스 검사(`test_services.py`)는 실행 범위 밖 |
| `scripts/demo/portfolio_demo.py --output artifacts/fable-r3-synthetic-20261023` | 성공. 활성 파티션 7, `failed_publish_kept_active_data: true`, `replay_hashes_identical: true`, batch 상태 committed 2 / failed 1, 보고서 `partial_period` 생성 | 격리 신규 폴더, 네트워크·Docker 없음 |
| `scripts/release/release.py check` | `Release declarations aligned: 0.5.4` | release.json ↔ Makefile/Compose/Helm/스크립트/pyproject/uv.lock/Airflow constraints SHA 일치 |

위 네 가지가 제가 직접 재현한 전부입니다. PostgreSQL/MinIO 통합 검사, kind/KPO, 공개 전체 처리, 병렬 측정, 화면 검사는 저자의 과거 근거(`docs/benchmarks/*.md`, `*.json`, `docs/releases/0.5.4.json`)를 읽고 일관성만 확인했으며 실행하지 않았습니다.

### 항목별 점수 (총 91 / 100)

| 영역 | 세부 항목 | 점수 | 근거 요약 |
|---|---|---:|---|
| 데이터 엔지니어링 (24/25) | 출처/단위/시간 계약 | 5 | `data-contract.md`, `ons-source-contract.md`, `data-sources.md`가 MD5/SHA·단위·시각 형식을 명시. `parquet.py:67-89`의 단일 UTC 파서와 regex, ONS `ts_utc=null`(`ons.py:200`). `test_bad_timestamps`, `test_offsets_are_utc` 재현. 비UTC 자정 전환 미검증은 `data-contract.md:47`에 명시 |
| | 파싱·정규화·충돌 | 5 | `source_bounds`(`pipeline.py:49-72`)가 요청 밖 행까지 Python 계약으로 검증, `deduplicate`가 동일키 상이값을 `DUPLICATE_CONFLICT`로 거부(`pipeline.py:84-94`), 중복 헤더·행 폭 검사(`brpvgen.py:66-89`), 인버터 ID 정규형(`parquet.py:22-29`). 관련 테스트 전부 재현 |
| | 품질 분모·unknown·0 | 5 | 분모 = 인버터별 관측 범위 ∩ 요청 날짜(`metrics.py:24-30`), 유효 0과 null 구분(`metrics.py:133`), 보간 불명 별도 집계(`metrics.py:50`), 보고서 `interpolation=null`(`render.py:75-80`). `test_series_distinguishes_invalid_zero_and_partial`, `test_entire_missing_dst_day_is_published` 재현 |
| | 증분/정정/철회 | 4 | BR: 명시 버전 upsert·`SOURCE_RANGE_SHRINK`·`--restore`(`pipeline.py:166-213, 246-249`). ONS: ETag 조건부 GET·월 cursor·`withdrawn` manifest(`ons.py:246-341`). 테스트 재현. 다만 개별 인버터 소실에 의한 분모 축소는 문서상 허용이며 manifest에 인버터 목록/범위가 없어 조회 경로에서 탐지 어려움(발견 2) |
| | 계보·결과 동등성 | 5 | 원본 SHA → source_object → run → active manifest → 보고서 `artifact_sha256`. 논리 해시에 run_id/시각 제외(`pipeline.py:395-409`). 제 데모에서 실패 후 재처리 7일 해시 동일 재현, `test_three_replays_identical` 통과 |
| 신뢰성 (23/25) | 원자 게시·실패 보존 | 5 | 객체 업로드 후 단일 트랜잭션에서 지표·active·metadata 전환(`pipeline.py:448-496`), 보고서 포인터 `update_if`(`render.py:144`), ONS cursor+manifest 동일 트랜잭션(`ons.py:297-340`). `before_commit`/`during_commit` 주입 테스트와 데모로 재현 |
| | 동시성·재시도 | 4 | 배치 시작 시 기대 active 캡처·조건부 교체(`pipeline.py:177-190, 457-471`), PG advisory lock(`pipeline.py:449-453`), `claim`의 ON CONFLICT DO NOTHING. SQLite 경쟁 테스트 재현. PostgreSQL 경로는 저자 근거(13통과)만 확인했고 직접 실행하지 않음 |
| | 조직/경로/비밀 경계 | 5 | 모든 조회에 `org_id`·시간대·계산 버전 조건, `identifier()` 제한, API 산출물 경로 루트 검사(`app.py:80-82`), 실패 코드 허용 목록으로 원문/DSN 미기록(`brpvgen.py:45-63`), 관리 서버 loopback/Origin/토큰(`admin/app.py:29-63`). `test_org_isolation`, sentinel 비노출 검사 재현. 조직 필터가 인증이 아님을 문서에 명시 |
| | 진단·복구 절차 | 4 | 읽기 전용 `inspect-runs`(`diagnostics.py`)와 `recovery.md`의 코드별 조치표, `FAILURE_RECORD_WRITE_FAILED` 경고. 다만 raw 체크섬 불일치가 `BR_INPUT_INVALID`로 분류되어 운영자를 잘못 안내(발견 1) |
| | 회귀 검사의 의미와 실제 실행 | 5 | 검사들이 실제 경쟁·주입 실패·부분 손상을 재현함(`test_publication_boundaries.py`, `test_integrity_boundaries.py`). 79통과 직접 실행. 문서가 skip 14건을 통과와 분리해 기록(`quality-v0.5.4.json`) |
| 아키텍처 (18/20) | 역할·공통 CLI | 5 | `cli.py` 단일 진입점, DAG는 CLI 인수만 조립하고 XCom 미사용(`solarops_factory.py:21-122`), Compose subprocess와 KPO가 같은 이미지·명령 |
| | 저장/조회 모델과 제약 | 4 | JSON payload + active 포인터 테이블, 읽기 전용 Catalog(`postgres.py:122-157`), 측정 후 PG 표현식 인덱스 추가. 단일 SELECT overview. `fleet_overview`의 source_kind 필터는 첫 객체만 보고 `snapshot`은 전체 객체를 보는 비대칭(ADR 0006에 전제 기록, ingest가 균일성을 보장하므로 결함은 아님) |
| | 기술 선택·비용·대안 | 5 | `technology-stack.md`가 버전·역할·대안·재검토 조건을 표로 제시. Kafka/Spark 미채택 이유, SQLite 비운영 명시, MinIO 소스 빌드 한계 명시 |
| | 배포 버전·설정과 운영 경계 | 4 | `release.json` 단일 명세와 `release.py check` 통과, Dockerfile digest 고정, `releases/0.5.4.json` 이미지 ID. ADR 0003이 `solarops-worker:0.4.0`·4개 DAG 시점 기술을 유지(발견 4) |
| 재현성 (13/15) | 새 환경의 작은 오프라인 시연 | 5 | 데모 직접 성공. 기존 경로 거부·새 폴더 생성(`portfolio_demo.py:24-26`). CI 양 OS에서 같은 스크립트 실행(`ci.yaml:28-29`) |
| | 의존성·실행 버전/이미지 추적 | 4 | uv.lock 고정, 베이스 이미지 digest, constraints SHA. 이미지 ID→커밋 연결은 저자 기록만 확인 가능. Airflow 전이 의존성은 버전 고정이지 hash 잠금이 아님(문서에 명시) |
| | 측정 절차·원본 요약·재현 한계 | 4 | 측정 조건·JSON 요약·재현 코드(`2026-10-23-bounds-reproduction.md`) 보존. 병렬 비교는 직렬/동시 각 1회로 통계적 근거가 약하나 한계를 정직하게 기술 |
| 전달력 (13/15) | 처음 보는 사람의 README 동선 | 4 | 빠른 실행 → 숫자 의미 → 설계 → 근거 → 범위 순서가 명확. 다만 본문이 길고 스킬·랜딩 안내가 핵심 동선에 섞여 있음 |
| | 주장과 코드/근거 연결 | 5 | 주장마다 benchmark md/json·코드 경로 링크, `check_docs.py`가 로컬 링크·스크립트 경로를 CI에서 검사 |
| | 현재 상태·과거 증거·미완료 구분 | 4 | "과거 근거" 표기, 버전별 benchmark 분리, 미검증 항목 명시. ADR 0003의 버전 표기 drift, README 표 일부가 v0.5.1 수치 인용(라벨은 있음) |

### 강점, 발견 사항, 검토 한계

**근거 있는 강점.**
- **실패 보존을 직접 재현.** 데모에서 커밋 중 주입 실패 뒤 활성 해시 7개가 유지되고 재처리 해시가 동일했습니다. 테스트는 실패 기록 자체의 2차 오류까지 원래 원인을 보존하는지 검사합니다(`test_pipeline.py:108-140`).
- **계약이 코드와 일치.** 분모·0/null·보간 불명·ONS 단위/시각 보존이 문서와 `metrics.py`, `ons.py`, `render.py`에서 같은 의미로 구현돼 있습니다.
- **비밀·원문 비노출.** 실패 코드 허용 목록, CLI 고정 문구, API의 DSN 제외를 테스트가 sentinel 값으로 검증합니다.
- **릴리스 선언 정합.** `release.py check`가 현재 커밋에서 통과했습니다.

**발견 사항과 최소 개선안.**
1. **raw 체크섬 불일치의 오류 코드 오분류.** `storage/minio.py:54,62,67`은 `ValueError("Immutable raw object checksum differs")`를 던지고, `contracts/brpvgen.py:55-56`이 모든 ValueError를 `BR_INPUT_INVALID`로 매핑합니다. 영향: 복사 중 원본 변경이나 S3 메타데이터 불일치 같은 저장소 무결성 문제가 "입력 오류"로 기록돼 `recovery.md`의 안내가 운영자를 입력 조사로 보냅니다. 정적 분석. 최소 개선: `ERROR_CODES`에 `RAW_OBJECT_CHECKSUM_MISMATCH`를 추가하고 메시지 접두어로 사용, `recovery.md` 표에 한 줄 추가. 기존 `test_changed_source_during_capture_never_publishes_bad_raw`는 `match="checksum"`이므로 메시지에 그 단어를 유지하면 수정 불필요.
2. **manifest에 인버터 목록/범위가 없음.** `data-contract.md:41`은 분모 축소를 "인버터 목록·원본 계보를 비교해" 판단하라고 하지만, `publish_day`의 manifest(`pipeline.py:423-440`)와 metric(`metrics.py:38-52`)에는 인버터 ID나 범위가 없어 Parquet를 열어야 합니다. 영향: 새 버전에서 인버터가 빠져 기대 슬롯이 절반이 돼도 API/보고서에서 신호가 없습니다(저자 근거 1,344→672). 정적 분석. 최소 개선: manifest에 `inverter_ids`와 ISO 문자열 범위를 추가(논리 해시 밖이므로 v2 유지)하고 보고서 일별 내역에 인버터 수를 표시.
3. **기상 파일의 요청 밖 행은 검증하지 않음.** `source_bounds`는 인버터 파일만 전수 검증하고(`pipeline.py:242`), 기상 행은 SQL `TRY_CAST` 필터(`parquet.py:52-57`)로 창 밖이면 조용히 제외됩니다. 계약(`data-contract.md:17`)이 "분모에 기여하는 행"만 약속하므로 위반은 아니지만 비대칭이 명시돼 있지 않습니다. 정적 분석. 최소 개선: 계약 문서에 한 문장 추가. 코드·테스트 변경 불필요.
4. **ADR 0003의 버전 표기 drift.** `docs/adr/0003-kpo-not-executor.md:3`이 `solarops-worker:0.4.0`과 4개 DAG 시점을 기술합니다. 영향: 릴리스 정렬을 읽는 독자가 혼동할 수 있음. 정적 분석. 최소 개선: "이미지 태그는 `release.json` 기준" 한 줄 추가. 영구 테스트 불필요.
5. **조회 경로의 source_kind 판정 비대칭(참고).** `readmodels.py:53,146`은 첫 source object만, `postgres.py:190-196`과 `freshness.py:58-64`는 전체 객체를 검사합니다. `ingest`가 세 파일에 같은 `source_kind`를 기록하므로(`pipeline.py:142,147`) 현재 데이터에서 결과 차이는 없습니다. 감점하지 않았으며, 조회 계약 문단에 전제를 한 줄 명시하면 충분합니다.

범위 밖(공개 배포·인증·다중 호스트 HA·상용 SLO)으로 감점한 항목은 없습니다. 확인된 계약 위반도 없습니다.

**검토 범위와 한계.**
- 읽은 범위: `AGENTS.md`, 루브릭, `README.md`, `src/solarops/` 전 모듈(API 정적 JS/HTML 제외), `tests/` 전체, `dags/solarops_factory.py`·`solarops_ons_daily.py`, `infra/compose|helm|docker`, `.github/workflows`, `docs/{data-contract,ons-source-contract,data-sources,IMPLEMENTATION_STATUS,README}.md`, `docs/architecture/*`, `docs/adr/*`, `docs/runbooks/*`, `docs/guides/*`, `docs/portfolio/{SUBMISSION,DEMO_GUIDE}.md`, `docs/benchmarks/{quality-v0.5.2~0.5.4,incremental-v0.5.0,stack-authenticity-20261023}.md/json`, `docs/releases/0.5.4.json`, `docs/worklog/2026-10-23-bounds-reproduction.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `Makefile`, `pyproject.toml`, `scripts/{release,demo}/*`, `scripts/validation/check_docs.py`.
- 읽지 않음: `handoff.md`, `plan.md`, 다른 리뷰, 다른 worklog, `.env`, `infra/generated`, `landing/`, 이미지, `.gitignore`/`skills-lock.json` 변경, `test_admin.py`·`test_workspace.py` 본문, 대시보드 JS.
- 작업 트리에 `README.md` 등 미커밋 수정이 있었습니다(git status 스냅샷). 제가 읽은 README는 작업 트리 버전이며 커밋 `36ac6ff` 내용과 다를 수 있습니다. 코드·테스트·인프라 파일은 수정 목록에 없었습니다.
- 네트워크·Docker·PostgreSQL/MinIO·kind는 사용하지 않았고, 추적 파일·기존 데이터를 변경하지 않았습니다. 새로 생성한 산출물은 `artifacts/fable-r3-pytest-20261023/`와 `artifacts/fable-r3-synthetic-20261023/`뿐입니다.
- 이 평가는 AI 판단이며 외부 감사·품질 보증을 대체하지 않습니다.