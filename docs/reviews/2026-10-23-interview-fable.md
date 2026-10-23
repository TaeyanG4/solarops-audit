# Fable — 독립 모의 면접관 평가

2026-10-23 (Asia/Seoul). 사용자가 지정한 Claude Code 경로로 호출했습니다. CLI `2.1.287`, 요청 별칭 `fable`, init와 응답에서 확인한 실제 모델 `claude-fable-5-1`. 세션 `2c9f8b53-0a1e-4630-a410-8a9ee5e83efb`, 기준 `66d63486722dfb7bc83418667c90db1cecfadbf6`입니다.

아래는 평가자의 최종 답변 전문입니다. 코드 위치는 평가 당시 행 번호입니다. 외부 사람의 채용 평가나 합격 확률을 뜻하지 않습니다. 일부 정적 판단은 본 세션의 재현으로 보완·정정했으므로 [교차 확인·종합 판단](2026-10-23-interview.md)을 함께 읽어야 합니다. [수행 기록](../worklog/2026-10-23-interview.md).

---

## 판단과 점수

**(1) 면접 초대 여부: 신입/주니어 데이터 엔지니어 기준 초대 권고. 미드레벨 기준은 보류.**

초대 이유는 코드가 문서의 주장을 실제로 뒷받침하기 때문입니다. 입력 계약, 원자적 일별 게시, 실패 보존, 논리 해시 재현성이 `src/solarops/pipeline.py`와 `src/solarops/storage/postgres.py`에 구현되어 있고, 같은 경계를 실패 주입과 스레드 경합으로 검사하는 테스트가 `tests/test_publication_boundaries.py`, `tests/test_integrity_boundaries.py`에 있습니다. 이전 독립 검토가 지적한 결함 네 가지는 현재 코드에서 모두 수정된 상태로 확인했습니다.

보류 사유는 두 가지입니다. 첫째, `CHANGELOG.md:3-92` 기준으로 전체 버전 이력이 이틀 안에 만들어졌고 `AGENTS.md`, `docs/development/skills.md`가 AI 도구 주도 개발을 명시합니다. 지원자 본인의 이해도는 면접에서 확인하기 전까지 알 수 없습니다. 둘째, 운영 범위가 단일 호스트 로컬 환경이며 인증, 정리 정책, 다중 노드는 문서 스스로 미검증으로 표시합니다. 포트폴리오 "100%"는 `plan.md:14-16`이 말하듯 제출 체크리스트 완료이지 품질 보증이 아닙니다.

**(2) 점수와 근거**

| 항목 | 점수 | 핵심 근거 |
|---|---|---|
| 데이터 엔지니어링 | 20/25 | 계약 검증, 품질 분류, 계보 |
| 신뢰성 | 20/25 | CAS 게시, 실패 보존, 실제 PG 검사 |
| 아키텍처 | 15/20 | 공통 CLI, 읽기 전용 API, JSON 중심 스키마 |
| 재현성 | 12/15 | 잠긴 의존성, digest 고정, 오프라인 데모 |
| 커뮤니케이션 | 10/15 | 한계 명시는 우수, 가독성과 외부 독자 배려 부족 |
| 합계 | 77/100 | |

데이터 엔지니어링 강점:
- **입력 계약이 코드로 강제됩니다.** 시간대 없는 시각, 15분 격자 밖 시각, 비정규 인버터 ID를 거부합니다. `src/solarops/normalize/parquet.py:22-29`, `:67-74`. 메타데이터의 중복 헤더와 행 폭 불일치도 거부합니다. `src/solarops/contracts/brpvgen.py:13-28`.
- **무효, 누락, 보간이 서로 다른 축으로 유지됩니다.** 무효는 원본 값 기준, 누락은 인버터별 관측 범위 대비, 보간은 별도 속성으로 집계합니다. `src/solarops/analytics/metrics.py:34-52`. 분모가 없으면 0이 아니라 None입니다. `metrics.py:47-49`.
- **월 집계가 비율 평균이 아니라 슬롯 가중입니다.** `src/solarops/api/readmodels.py:39-48`, 검사 `tests/test_workspace.py:83`.
- **ONS는 원문 시각과 MWmed를 보존하고 UTC 변환이나 kWh 합산을 하지 않습니다.** `src/solarops/acquisition/ons.py:38-51`, `:165-173`. 검증/예측/미확정 분류와 철회 처리가 테스트됩니다. `tests/test_contracts.py:49-83`, `tests/test_publication_boundaries.py:199-251`.
- **계보가 두 층으로 분리됩니다.** 원본 SHA 기반 불변 raw 보존은 `src/solarops/storage/minio.py:42-73`, 실행 ID를 제외한 논리 해시는 `pipeline.py:381-395`입니다.

신뢰성 강점:
- **활성 포인터 교체가 조건부입니다.** 배치 시작 시점의 기대 run_id로 UPDATE … RETURNING을 수행하고 불일치 시 실패합니다. `pipeline.py:171-184`, `:443-457`. 메타데이터도 같은 트랜잭션에서 검사합니다. `:460-466`.
- **ONS 성공 cursor와 변경 날짜가 같은 트랜잭션에서 전환됩니다.** `ons.py:264-307`. 실패하면 이전 cursor가 남는 것을 검사합니다. `tests/test_publication_boundaries.py:224-227`, `:290-298`.
- **실패 경로가 증거를 남깁니다.** quarantine.json과 단계별 상태 기록 `pipeline.py:490-495`, 읽기 전용 진단 `src/solarops/diagnostics.py`.
- **실제 PostgreSQL/MinIO 검사가 선택형으로 존재합니다.** `tests/test_services.py:37-142`, `.github/workflows/services.yaml`.

아키텍처와 재현성 강점:
- DAG는 CLI만 호출하고 변환 로직을 복제하지 않습니다. `dags/solarops_factory.py:21-122`. Pod 보안 컨텍스트와 자원 한도가 명시됩니다. `:78-86`.
- API는 읽기 전용 카탈로그를 사용하고 스키마나 버킷을 생성하지 않습니다. `postgres.py:122-148`, `tests/test_integrity_boundaries.py:61-105`.
- 기반 이미지가 digest로 고정되고 릴리스 명세와 이미지 ID가 연결됩니다. `infra/docker/Dockerfile:1-2,17`, `docs/releases/0.5.1.json`.
- CI가 두 OS에서 lint, 테스트, 합성 데모, 복원 드릴, 패키징, lock 불변을 한 번에 검사합니다. `.github/workflows/ci.yaml:18-33`.

## 우려 사항

**(3) 상위 우려, 분류와 심각도**

1. **정적 확인 결함, 낮음: ONS 실패 기록이 원인 코드를 잃습니다.** `ons.py:376`은 `error_code`에 예외 클래스 이름만 저장합니다. 스키마 변경, 시각 오류, cursor 충돌이 모두 "ValueError"로 기록되어 UI와 API의 최근 시도 목록에서 구분할 수 없습니다. BR-PVGen 경로는 `pipeline.py:298`에서 메시지 접두사를 보존하므로 두 경로가 불일치합니다. 실행으로 재현하지는 않았습니다.
2. **정적 확인 불일치, 낮음: 보고서의 분모 0 처리가 문서 주장과 다릅니다.** `src/solarops/reports/render.py:66-75`는 분모가 0이면 0을 반환하는데 `docs/portfolio/CASE_STUDY.md:54`는 0으로 바꾸지 않는다고 설명하고 `readmodels.py:43-47`은 None을 반환합니다. 게시 조건상 분모 0인 파티션은 사실상 생기지 않아 실질 영향은 없습니다.
3. **정적 확인 불일치, 낮음: 관측 범위 계산과 정규화의 시각 처리가 다릅니다.** `pipeline.py:58`은 DuckDB TRY_CAST로 시간대 없는 시각을 UTC로 받아들이지만 `parquet.py:70-71`은 같은 행을 거부합니다. 요청 구간 밖의 시간대 없는 행은 조용히 기대 범위를 넓히고, 구간 안이면 전체 실패입니다. 실제 BR-PVGen이 Z 접미사를 쓰므로 발생 여부는 불확실합니다.
4. **운영 범위 한계, 중간: ONS 중복 충돌이 월 전체를 중단합니다.** `ons.py:174-177`은 같은 entity와 시각에 다른 내용이 있으면 월 게시를 포기합니다. 같은 id_ons가 다른 운영 모드로 두 번 나오면 발생할 수 있습니다. 보수적 선택이지만 복구는 수동입니다. 실제 자료에서 발생했는지는 확인하지 못했습니다.
5. **운영 범위 한계, 중간: 정리 정책이 없습니다.** staging과 quarantine 디렉터리, 완료 Pod가 보존만 됩니다. `dags/solarops_factory.py:89`, `docs/adr/0008-storage-integrity.md:19`. 문서가 인정하지만 장기 운영 시 디스크와 클러스터 자원을 소모합니다.
6. **운영 범위 한계, 중간: 일별 재처리가 발전소 파일 전체를 매번 스캔합니다.** `pipeline.py:236-246`과 `parquet.py:43-64`는 하루를 처리해도 전체 CSV를 세 번 읽습니다. 벤치마크 JSON의 S3 신규 바이트가 그 비용을 보여줍니다. `docs/benchmarks/incremental-v0.5.0.json:46-47`. 현재 규모에서는 문제가 아니지만 확장 질문의 대상입니다.
7. **운영 범위 한계, 낮음: 스키마가 JSON payload 중심이고 페이지네이션이 메모리에서 이뤄집니다.** `postgres.py:27-34`는 모든 테이블을 키와 JSON payload로 정의하고, `src/solarops/api/app.py:177-190`은 발전소 전체 이력을 읽은 뒤 Python에서 슬라이스합니다. 인덱스 두 개로 보완했지만 관계형 모델링 경험을 보여주지는 못합니다.
8. **면접 위험, 높음: 본인 이해도가 미확인입니다.** 이틀 안에 수십 개 문서와 다섯 번의 릴리스가 만들어졌고 AI 도구 사용이 공개되어 있습니다. 설계 선택을 코드 라인까지 직접 설명할 수 있는지 확인해야 합니다.
9. **면접 위험, 중간: 문서 가독성과 외부 독자 배려.** `README.md:118`, `handoff.md:13`은 외부 독자가 열 수 없는 localhost 링크를 포함합니다. "로컬136통과·14제외" 같은 띄어쓰기 없는 숫자 나열이 README 전반에 반복됩니다. 신뢰성 수치가 많아도 읽는 사람의 부담이 큽니다.
10. **면접 위험, 낮음: 성능 헤드라인의 범위.** 직렬 대비 동시 2의 단축은 각 1회 측정이며 `docs/benchmarks/incremental-v0.5.0.md:43`이 이를 명시합니다. 지원자가 이 수치를 일반 처리 성능으로 말하면 감점 요인입니다.

구분해서 봐야 할 점: BR-PVGen 계보와 추정 kWh는 검증된 산식이고, 무효/누락/보간은 서로 다른 지표이며, ONS는 단위와 시간대 불확실성 때문에 의도적으로 분리된 별도 자료입니다. 이 넷을 섞어 설명하는 답변은 약한 답변입니다.

## 질문, 개선, 검토 범위

**(4) 면접 질문 다섯 개와 강한 답변의 조건**

1. 객체 업로드 후 DB 커밋이 실패하면 디스크, S3, DB에 각각 무엇이 남고 어떻게 찾습니까? `pipeline.py:399-495`. 강한 답변은 run_id 기반 staging 경로, quarantine.json, 상태 failed와 stage 필드, active 불변, 재시도가 새 run_id를 만든다는 점, 그리고 분산 트랜잭션을 쓰지 않은 이유를 설명합니다.
2. 월 유효값 비율을 일별 비율 평균으로 계산하지 않는 이유와 보간 슬롯을 복원하는 방식의 한계는 무엇입니까? `readmodels.py:29-48`. 강한 답변은 슬롯 가중 합, 인버터별 관측 범위가 분모인 이유, None과 0의 의미 차이, `round(ratio × observed)` 복원이 손실 있는 근사라는 점을 짚습니다.
3. ONS의 ts_utc가 null인 이유와, UTC와 에너지로 변환하려면 무엇이 더 필요합니까? `ons.py:38-51`. 강한 답변은 시간대와 구간 기준 미명시, MWmed가 시간 평균이라 시간 단위 구간 가정이 있어야 MWh가 된다는 점, 철회 날짜 표현, 중복 충돌 시 월 전체 중단이라는 트레이드오프를 말합니다.
4. `make_ons_dag`의 `data_interval_end`가 Airflow 3에서 무엇을 뜻하고 catchup=False와 어떻게 상호작용합니까? `dags/solarops_factory.py:221-244`. 강한 답변은 cron trigger 타임테이블에서 실행 시각과 같다는 점, 이전/현재 월 재확인 설계, keep_pod의 비용, 그리고 `replay.py:98-105`의 fail-once marker가 공유 PVC에 의존함을 설명합니다.
5. `claim`과 advisory lock, `--restore`는 각각 어떤 경합을 막습니까? `postgres.py:107-119`, `pipeline.py:203-207`, `:435-439`. 강한 답변은 ON CONFLICT DO NOTHING RETURNING의 의미, 잠금 범위가 조직과 발전소 단위인 이유, SQLite에서 읽기 후 쓰기 경합을 테스트로 강제한 방법 `tests/test_integrity_boundaries.py:155-195`, 과거 버전 복원이 기본 거부인 이유를 포함합니다.

추가로 "이 저장소에서 본인이 직접 결정하고 작성한 부분은 어디이며, AI 제안을 거부한 사례는 무엇인가"를 반드시 물어야 합니다.

**(5) 최소 우선 개선**

1. `ons.py:376`의 `error_code`를 `pipeline.py:298`과 같은 메시지 접두사 방식으로 통일합니다. 한 줄 변경입니다.
2. `render.py:66-75`의 분모 0 처리를 None으로 맞추거나 문서를 코드에 맞춥니다.
3. `pipeline.py:48-66`의 관측 범위 계산에서 시간대 없는 시각을 명시적으로 거부하거나 정규화와 같은 규칙으로 처리합니다.
4. README를 외부 독자용으로 분리합니다. localhost 링크와 이 PC 상태는 handoff로 옮기고, 숫자 나열에 띄어쓰기를 넣고, 한 쪽 요약을 첫 화면에 둡니다.
5. 보고서 시간대 결정을 ADR로 남깁니다. Compose 환경 변수에 보고서 시간대가 없어 브라질 발전소가 UTC 일자로 분할됩니다. `infra/compose/compose.yaml:2-10`, `src/solarops/config.py:26`. 결함은 아니지만 설명할 수 있어야 합니다.
6. 선택: ONS 중복 충돌 시 월 전체 중단 대신 해당 날짜만 격리하는 정책을 검토합니다. 설계 토론 과제로 적합합니다.

**(6) 읽은 것과 검증하지 못한 것**

읽은 파일: `AGENTS.md`, `handoff.md`, `plan.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml`, `docs/portfolio/SUBMISSION.md`, `CASE_STUDY.md`, `DEMO_GUIDE.md`, `DESIGN_QUESTIONS.md`, `docs/architecture/system.md`, `technology-stack.md`, `docs/data-contract.md`, `docs/ons-source-contract.md`, `docs/data-sources.md`, `docs/guides/data-ingestion.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/adr/0003`, `0007`, `0008`, `docs/reviews/2026-10-23-independent.md`, 벤치마크 문서 `2026-10-22.md`, `reliability-v0.4.0.md`, `integrity-v0.4.2.md`, `technical-20261023.md`, `stack-authenticity-20261023.md`, `incremental-v0.5.0.md`와 JSON, `portfolio-finish-20261023.md`, `docs/worklog/README.md`, `2026-10-23-incremental.md`, `docs/releases/0.5.1.json`. 소스는 `src/solarops` 하위 `pipeline.py`, `replay.py`, `config.py`, `runtime.py`, `cli.py`, `fixtures.py`, `diagnostics.py`, `analytics/metrics.py`, `contracts/brpvgen.py`, `contracts/dates.py`, `normalize/parquet.py`, `storage/postgres.py`, `storage/minio.py`, `acquisition/brpvgen.py`, `acquisition/ons.py`, `reports/render.py`, `reports/freshness.py`, `api/app.py`, `api/readmodels.py`, `admin/app.py`, `release.json`. 테스트는 `conftest.py`, `test_pipeline.py`, `test_publication_boundaries.py`, `test_integrity_boundaries.py`, `test_contracts.py`, `test_calculation_v2.py`, `test_workspace.py`, `test_services.py`, `test_replay.py`, `test_api_validation.py`, `test_diagnostics.py`, `test_packaging.py`. 인프라와 스크립트는 `dags/solarops_factory.py`, `solarops_ons_daily.py`, `infra/docker/Dockerfile`, `infra/compose/compose.yaml`, `.github/workflows/ci.yaml`, `services.yaml`, `scripts/demo/portfolio_demo.py`, `scripts/validation/k8s_benchmark.py`, `scripts/validation/check_docs.py`, `scripts/data/full_dataset.py`. `dashboard.js`는 ONS API 호출 존재만 grep으로 확인했습니다.

실행하지 않은 것: 테스트, CLI, 브라우저, Docker, Kubernetes, 네트워크 호출을 전혀 실행하지 않았습니다. 따라서 테스트 통과 수, CI 결과, 비공개 GitHub 저장소 상태, DB와 MinIO의 실제 내용, Airflow 일정 활성 여부, 성능 수치, 스크린샷 내용은 문서의 주장으로만 알고 있으며 검증하지 못했습니다. Git 제외 `artifacts/`와 `data/`는 읽지 않았습니다. `.env`, 자격 증명, 원본 데이터셋은 읽지 않았습니다. 위 결함 세 가지는 코드 읽기로 식별한 것이며 실행으로 재현한 결과가 아닙니다. `test_admin.py`, `dashboard.js` 본문, Helm 값 파일, `docs/runbooks/*`는 읽지 않았습니다.
