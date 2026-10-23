## 1. 검토 범위와 실행하지 않은 검사

검토 커밋은 `adc75001360a767f9d10ed4066d42a31a0b6abf0`이며, 구현 커밋 `39a56e76…`과 `src/solarops/release.json`, `pyproject.toml`, `uv.lock`, `docs/releases/0.5.2.json`의 버전 0.5.2 선언이 서로 일치함을 확인했습니다.

**직접 읽은 범위**
- 코드: `src/solarops/` 전체 29개 모듈 중 정적 자산과 대시보드 JS를 제외한 전부. 보고서 템플릿 `monthly.html` 포함.
- 테스트: `tests/` 14개 파일 전부. 테스트 함수 86개를 확인했고 매개변수화를 포함한 150건 집계는 문서 수치를 그대로 인용합니다.
- 인프라·운영: `dags/` 전부, `infra/compose/compose.yaml`, `infra/docker/Dockerfile`, `Dockerfile.minio`, `infra/helm/airflow-values.yaml`, `infra/k8s/services.yaml`, `.github/workflows/*`, `Makefile`, `.gitignore`.
- 스크립트: 데모, 복원 드릴, 벤치마크, 전체 처리, 릴리스 검사, DAG 검증, 비밀 생성 스크립트.
- 문서: README, 루브릭, 데이터·ONS 계약, 아키텍처·기술 선택, 설치·수집 가이드, runbook 3개, ADR 5개, 벤치마크 8개, 릴리스·이미지 JSON, handoff, 구현 상태, CHANGELOG, CONTRIBUTING, 제출 요약·사례·시연 가이드.

**읽지 않은 것**: `docs/reviews/`의 과거 평가 원문 3개, `plan.md`, `docs/plan/`, `docs/market/`, `docs/design/`, 대시보드 JS/CSS, 브라우저 검증 스크립트, `airflow_checks.py`, `service_restore_drill.py`, `.env*`, `infra/generated/`. handoff와 worklog에 목표 점수 문구가 있었으나 항목별 점수는 코드와 근거만으로 매겼습니다.

**실행하지 않은 검사**: pytest, Ruff, 합성 데모, CI, Docker/kind/Helm, HTTP 호출. 아래 모든 통과 수치는 저장소 문서와 CI 실행 ID의 기록이며 제가 재실행한 결과가 아닙니다.

## 2. 총점 95 / 100

| # | 영역·항목 | 점수 | 근거 |
|---|---|---:|---|
| 1 | 출처/단위/시간 계약 | 5 | `normalize/parquet.py:67-81`의 단일 UTC 파서, `acquisition/ons.py:38-51`의 MWmed·시간대 미명시 계약, `docs/data-contract.md`·`ons-source-contract.md`와 일치. `tests/test_contracts.py:49-83,111-122` |
| 2 | 파싱·정규화·충돌 | 5 | ID 정규화 `parquet.py:22-29`, DuckDB 외부 정렬 `parquet.py:43-64`, 동일키 상이값 거부 `pipeline.py:84-94`, metadata 열 폭 검사 `contracts/brpvgen.py:13-28`, ZIP 안전 추출 `acquisition/brpvgen.py:94-141`. `tests/test_integrity_boundaries.py:23-35`, `test_contracts.py:147-165` |
| 3 | 품질 분모·unknown·0 | 5 | 인버터별 범위 교집합 분모 `analytics/metrics.py:24-52`, 무효만 있는 슬롯 null `metrics.py:131-135`, 관측 0일 때 보간율 null `reports/render.py:72-77`·`monthly.html:22`, 슬롯 가중 집계 `api/readmodels.py:39-48`. `tests/test_calculation_v2.py`, `test_workspace.py:62-99` |
| 4 | 증분/정정/철회 | 5 | 조건부 GET·부분 응답 거부 `ons.py:108-134`, 날짜 해시 비교·철회 manifest `ons.py:246-294`, cursor CAS 커밋 `ons.py:297-340`, 소스 버전 충돌·복원 플래그 `pipeline.py:166-213`. `tests/test_publication_boundaries.py:199-357`, 실제 수집 기록 `docs/benchmarks/incremental-v0.5.0.md` |
| 5 | 계보·결과 동등성 | 5 | 논리 해시 구성 `pipeline.py:387-401`, manifest의 원본 SHA·release·execution `pipeline.py:415-432`, 보고서 근거 비교 `reports/freshness.py`. 12,572 파티션 v1/v2 대조 `reliability-v0.4.0.md`, 7일 해시 동등 `quality-v0.5.2.json` |
| 6 | 원자 게시·실패 보존 | 5 | 객체 업로드 후 단일 트랜잭션 `pipeline.py:440-488`, 실패 시 quarantine·failed 기록 `pipeline.py:496-501`, 보고서 포인터 조건부 전환 `render.py:129-143`. `test_pipeline.py:72-85`, `test_publication_boundaries.py:114-197`, PostgreSQL 재사용 `test_services.py` |
| 7 | 동시성·재시도 | 5 | advisory lock·기대 run_id 조건부 UPDATE `pipeline.py:441-463`, claim의 RETURNING 판별 `storage/postgres.py:107-119`. 겹친 배치 경합 `test_publication_boundaries.py:19-62`, SQLite 실제 레이스 `test_integrity_boundaries.py:155-195`, Airflow 재시도 2회 `dags/solarops_factory.py:144-149` |
| 8 | 조직/경로/비밀 경계 | 5 | 식별자 정규식 `config.py:13-15`, 아티팩트 경로 루트 한정 `api/app.py:79-82`, 소스 루트 이탈 거부 `replay.py:49-53`, 관리 서버 Host·Origin·토큰 `admin/app.py:29-63`, 오류 메시지 제한 `cli.py:124-138`·`ons.py:75-89`. `.gitignore`의 `.env`·`infra/generated/`. `test_admin.py:192-247`, `test_pipeline.py:118-131` |
| 9 | 진단·복구 절차 | 4 | 읽기 전용 `diagnostics.py`, 원인 코드 표 `docs/runbooks/recovery.md:27-35`, CI 복원 드릴 `ci.yaml:30`. 감점: ONS `collection_run`의 멈춘 running 기록은 `inspect-runs`가 다루지 않고 수동 대조만 안내 |
| 10 | 회귀 검사 의미·실행 | 5 | 결함 재현형 테스트가 다수이며 동일 함수를 PostgreSQL/MinIO에 재사용 `test_services.py:18-34`. 두 OS CI `ci.yaml`, 선택형 서비스 CI `services.yaml`. 통과 수치는 기록 인용 |
| 11 | 역할·공통 CLI | 5 | 단일 진입점 `cli.py`, DAG는 CLI 인수만 조립 `solarops_factory.py:21-122`, Compose/KPO 동일 이미지 `compose.yaml:49-66` |
| 12 | 저장/조회 모델·제약 | 5 | payload 테이블과 active 포인터 `postgres.py:27-86`, 읽기 전용 Catalog `postgres.py:122-158`, 단일 SELECT 집계 `readmodels.py:51-124`, 실측 인덱스 `technical-20261023.md`. 한계 명시 |
| 13 | 기술 선택·비용·대안 | 5 | `docs/architecture/technology-stack.md`의 버전·대안·재검토 조건, ADR 0001·0002·0003 |
| 14 | 배포 버전·설정·운영 경계 | 4 | 단일 명세 `release.json`과 CI 드리프트 검사 `release.py:15-56`, digest 고정 `Dockerfile:1-2,17`. 감점: `Makefile:39`의 이미지 태그 0.4.1이 검사 범위 밖 |
| 15 | 새 환경 오프라인 시연 | 5 | `scripts/demo/portfolio_demo.py`의 실행형 단언, CI가 두 OS에서 실행 `ci.yaml:28-29` |
| 16 | 의존성·버전/이미지 추적 | 4 | 고정 의존성과 lock 검사 `ci.yaml:33`, 이미지 ID 기록 `docs/releases/0.5.2.json`. 감점: `Dockerfile.minio:4` 소스 tarball 체크섬 없음, `:2,7` 기반 이미지 태그만 고정 |
| 17 | 측정 절차·원본 요약·한계 | 4 | 벤치마크마다 조건·한계·JSON 요약, 재현 스크립트 `k8s_benchmark.py`. 감점: v0.5.2 범위 계산 비용 측정은 저장소에 스크립트가 없어 재현 불가 |
| 18 | README 동선 | 5 | 요약, 빠른 실행, 숫자 의미, 설계, 근거·한계, 구조 순서. 각 주장에 문서 링크 |
| 19 | 주장과 코드/근거 연결 | 5 | `CASE_STUDY.md:19-28` 표가 테스트·코드에 직접 연결. 테스트 수·이미지 ID·릴리스 버전을 대조해 불일치 없음 |
| 20 | 현재/과거/미완료 구분 | 4 | handoff·구현 상태·CHANGELOG가 버전별로 분리. 감점: `docs/architecture/system.md:7,138`이 현재 앱을 v0.5.1로 기술 |

영역 합계는 데이터 25, 신뢰성 24, 아키텍처 19, 재현성 13, 전달력 14입니다.

## 3. 발견 문제

**확인된 결함** 은 코드 읽기로 확정한 것이며, 모두 실행 없이 정적 추론으로 재현 가능한 수준입니다.

- **중간, `Makefile:39`.** `dag-validate`가 `solarops-airflow:0.4.1` 이미지를 사용합니다. `validate_dags.py:9-18`은 DAG 7개를 요구하는데 0.4.1 이미지에 구운 DAG 폴더에는 ONS·벤치마크 DAG가 없으므로 이 명령은 실패하거나 잘못된 이미지를 검증합니다. `setup.md:50`이 이 명령을 안내합니다. `release.py:21-29`의 검사 경로에 Makefile이 없어 CI도 잡지 못합니다. 실행으로 확인하지는 않았습니다.
- **낮음, `docs/architecture/system.md:7,138`.** 현재 앱을 v0.5.1로 기술하고 0.5.1 릴리스 파일을 최신으로 링크합니다. README·handoff·구현 상태는 v0.5.2라서 독자가 두 버전 중 무엇이 배포됐는지 혼동합니다.

**문서화된 공백** 은 저장소가 스스로 한계로 밝힌 것이며 점수에는 반영했습니다.

- `infra/docker/Dockerfile.minio:4`가 `ADD https://…tar.gz`에 체크섬을 두지 않고, 기반 이미지도 태그만 고정합니다. `technology-stack.md:13`에 한계로 기록돼 있습니다.
- `inspect-runs`는 `pipeline_run`만 조회합니다. `ons-status`가 running 시도를 보여주지만 복구 runbook은 수동 대조를 요구합니다.
- `quality-v0.5.2.md:13,19`의 범위 계산 전후 비교는 임시 스크립트로 수행했고 저장소에 남기지 않았습니다.

**정적 관찰, 결함 아님**

- `pipeline.py:304`는 예외 문자열 앞부분을 error_code로 저장합니다. 전력값 `float()` 실패 같은 경우 `could not convert string to float`처럼 도메인 코드가 아닌 문자열이 남습니다. 값은 노출되지 않습니다.
- `ons.py:364`의 `metadata["result"]` KeyError는 `ONS_UNEXPECTED_ERROR`로 기록됩니다. 의미상 `ONS_SOURCE_CONTRACT_CHANGED`가 더 정확합니다.
- `readmodels.py:53`은 첫 source object의 종류로 필터하고 `postgres.py:190-196`은 모든 object 일치를 요구합니다. 현재 입력 구조상 결과는 같습니다.
- `solarops_factory.py:89`의 `keep_pod`는 완료 Pod를 누적합니다. ADR 0003에 의도로 기록돼 있습니다.

## 4. 감점 사유별 최소 개선

- **항목 14:** `release.py:21-29` 경로 목록에 `Makefile`을 추가하고 `sync`로 태그를 맞추면 됩니다. 새 도구는 필요 없습니다.
- **항목 20:** `system.md:7,138` 두 줄을 v0.5.2와 `releases/0.5.2.json`으로 갱신하거나 버전 문구를 handoff 링크로 대체합니다.
- **항목 16:** `Dockerfile.minio`의 `ADD`에 `--checksum=sha256:…`를 붙이고 두 기반 이미지를 digest로 고정합니다.
- **항목 17:** v0.5.2 범위 계산 비교에 쓴 스크립트를 `scripts/validation/`에 넣거나, 문서에 재현 불가 측정임을 한 줄로 명시합니다.
- **항목 9:** `inspect_runs`가 `collection_run`의 running 기록도 같은 목록에 포함하도록 확장하거나, 최소한 `recovery.md`에 `ons-status` 조회를 멈춘 수집 확인 절차로 명시합니다.

데이터 계약, 원자 게시, 동시성, 경계 테스트, README 동선은 현재 근거로 충분하며 추가 도구나 시험을 권하지 않습니다.

## 5. 산정 원칙

만점 항목은 코드·테스트·기록이 서로 일치하고 제가 읽은 범위에서 미해결 문제를 찾지 못한 경우에만 부여했습니다. 고객 인증, 공개 배포, 다중 호스트 고가용성, 특정 도구 유무는 감점 사유로 쓰지 않았습니다. 이 점수는 정적 검토 결과이며 테스트·CI·배포 통과를 제가 직접 확인한 것이 아닙니다.