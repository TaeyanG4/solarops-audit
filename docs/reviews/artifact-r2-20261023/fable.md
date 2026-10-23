## 검토 커밋과 읽은 범위

- **평가 대상:** `H:/dev/solarops_audit`, 고정 커밋 dbfb04ca4a3a9bf7c0f9e2b7de552079b2312cf5. 구현 커밋 038a000b69befaa77efd918a0b9654ba866ce501, 앱 v0.5.3, 계산 `energy-interval-v2`.
- **평가자·도구:** Claude Fable 5.1, Read/Glob/Grep만 사용. 테스트·데모·컨테이너·API를 실행하지 않았습니다. 아래의 모든 "통과" 수치는 저장소에 보존된 자기 보고 기록이며 제가 재실행한 결과가 아닙니다.
- **읽은 파일:** README, AGENTS, CHANGELOG, CONTRIBUTING, pyproject, uv.lock 존재 확인, `.gitignore`, CI 두 워크플로, Makefile, Dockerfile 2종, compose.yaml, Helm values, k8s services.yaml, DAG factory·ONS DAG, release.json과 docs/releases/0.5.3.json, `src/solarops` 전체 모듈(pipeline, contracts, normalize, analytics, storage, acquisition brpvgen/ons, replay, cli, reports render/freshness/템플릿, api app/readmodels, diagnostics, runtime, config, fixtures, admin app/services), tests 13개 파일 전부, scripts 중 demo/release/validate_dags/service-test/check_docs/backup_restore_drill/bootstrap, docs의 data-contract, ons-source-contract, data-sources, architecture 2종, ADR 0002/0003/0007/0008, guides setup/data-ingestion, runbooks recovery/dags/backup-restore, portfolio SUBMISSION/DEMO_GUIDE/CASE_STUDY, benchmarks quality-v0.5.3.md/json, quality-v0.5.2.md, incremental-v0.5.0.md, portfolio-finish, integrity-v0.4.2, stack-authenticity, 2026-10-22.md, IMPLEMENTATION_STATUS, docs/README, worklog 2026-10-23-bounds-reproduction.md, reviews/portfolio-rubric.md.
- **읽지 않은 것:** handoff.md, plan.md, docs/reviews의 루브릭 외 파일, 다른 worklog, artifacts, `.env`, `infra/generated/`, skills-lock.json, `.taste-skill/`, `landing/`. 전역 grep에서 handoff.md와 plan.md의 링크 한 줄씩이 노출됐으나 점수·목표 정보는 없었고 파일을 열지 않았습니다.

## 총점 90/100과 세부 점수

| # | 항목 | 점수 | 근거 |
|---|---|---:|---|
| 1 | 출처/단위/시간 계약 | 5 | BR-PVGen MD5/SHA·DOI·CC BY, ONS MWmed·`ts_utc=null`·라이선스 버전 미명시가 `data-contract.md`, `ons-source-contract.md`, `ons.py` CONTRACT 상수와 일치. 시각 형식은 `parquet.py:77-82` 정규식으로 고정되고 `test_contracts.py:111-129`가 7개 불량 형식을 범위 계산과 정규화 양쪽에서 검사. |
| 2 | 파싱·정규화·충돌 | 5 | 동일키 상이값 거부(`pipeline.py:84-94`), 인버터 ID canonical int64, SQL 파싱 불가행 NULLS FIRST 우선 검증, 전체 원본 행을 Python 파서로 재검증하는 `source_bounds`. 메타데이터 중복 헤더·행 폭 검사와 테스트 존재. |
| 3 | 품질 분모·unknown·0 | 4 | 분모는 인버터별 원본 범위와 날짜의 교집합이고 전부 무효 슬롯은 null, 관측 0일 때 비율 null. 다만 전부 불명인 날의 일별 `source_interpolation_ratio`는 0.0으로 저장되며 CSV·metrics API에 그대로 노출되고 HTML·대시보드만 매크로로 "알 수 없음" 보정(문제 P2). 인버터 단위 소실로 분모가 줄어도 거부하지 않음(P1). |
| 4 | 증분/정정/철회 | 4 | ONS는 ETag 조건부 GET, 날짜 hash 비교, withdrawn manifest, 기대 run_id 비교 cursor 전환을 `test_publication_boundaries.py:199-357`에서 검사. BR은 upsert이며 철회 미지원을 명시하고 `SOURCE_RANGE_SHRINK`로 발전소 단위 범위 축소를 거부. 인버터 단위 축소는 미검출(P1). |
| 5 | 계보·결과 동등성 | 5 | 원본 SHA-256, run_id 제외 논리 해시, 일별 manifest, 보고서 `source_manifest_hash`와 freshness 비교. 3회 재처리 동일·실패 후 해시 보존·series 변경 시 해시 변경 테스트. 공개 하루를 CSV 독립 계산까지 추적한 기록 보존. |
| 6 | 원자 게시·실패 보존 | 5 | 객체 선저장 후 단일 트랜잭션으로 지표·active·metadata 전환(`pipeline.py:447-495`). 실패 staging·quarantine 보존, 보고서 업로드/DB 실패와 역순 완료 검사, ONS 커밋 중 실패 시 cursor 보존 검사. |
| 7 | 동시성·재시도 | 4 | PG advisory lock, RETURNING 기반 조건부 교체, 버전 claim의 SQLite 실제 경합 테스트, 겹친 배치 3모드 테스트. 한계: PG 검사는 opt-in 워크플로, SQLite 직렬화는 선행 INSERT의 암묵 잠금에 의존(주석만 존재), 보고서 포인터는 호스트 시계 동기화 가정. |
| 8 | 조직/경로/비밀 경계 | 5 | 모든 조회가 프로세스 org로 제한, 산출물 경로는 root 하위 검사, 식별자 정규식, 오류 코드 허용 목록과 sentinel 비노출 테스트(`test_pipeline.py:88-107`), `.env`·generated 디렉터리 ignore, 관리 서버는 Host·Origin·토큰·loopback 검사와 docker 허용 목록. |
| 9 | 진단·복구 절차 | 4 | 읽기 전용 `inspect-runs`, 오류 코드별 조치 표, SQLite·PG/MinIO 복원 드릴. 한계: ONS stale running은 수동 kubectl 절차만 있고, 실패 기록 저장 자체가 DB 오류로 실패하면 원인 코드가 유실됨(P4). |
| 10 | 회귀 검사의 의미와 실제 실행 | 4 | 테스트는 경계 실패를 직접 주입(장애·경합·변조·누출). CI는 양 OS에서 pytest·데모·복원·패키징 실행. 다만 154통과·CI 성공·서비스 13통과는 자기 보고이며 본 평가에서 미실행, 서비스 검사는 정기 CI 밖. |
| 11 | 역할·공통 CLI | 5 | 단일 `cli.py` 진입점, DAG는 CLI 인수만 렌더링하고 변환 로직 없음, Compose·KPO 동일 이미지, `validate_dags.py`가 7 DAG 템플릿 검사. |
| 12 | 저장/조회 모델과 제약 | 4 | PK·unique·active 포인터·read-only URL·월 범위 단일 SELECT와 쿼리 수 테스트. JSON payload 중심이라 FK가 없고 `source_objects[0]` JSON 인덱스로 종류를 필터하며, 대용량 이력 비용은 문서상 측정 후 보강으로 유보. |
| 13 | 기술 선택·비용·대안 | 5 | 버전·역할·대안·재검토 조건 표, Kafka/Spark 미도입 이유, MinIO 소스 빌드 사유와 AGPL 명시, 메모리 한도가 전체 프로세스 보장이 아님을 명시. |
| 14 | 배포 버전·설정과 운영 경계 | 4 | release.json 단일 명세, CI의 `release.py check`, 기반 이미지 digest, 이미지 ID 기록. 한계: 실행 중 MinIO는 digest 고정 전 빌드이고 태그가 동일(P6), Helm chart app_version과 실제 Airflow 불일치, Airflow 전이 의존성은 해시 잠금 아님. 모두 문서화됨. |
| 15 | 새 환경의 작은 오프라인 시연 | 5 | `portfolio_demo.py`가 새 폴더에서 정상·실패 주입·보존 확인·재처리 동등·보고서를 assert로 검증하고 CI 양 OS에서 실행. 비공개 저장소 접근과 최초 의존성 네트워크 필요는 명시. |
| 16 | 의존성·실행 버전/이미지 추적 | 5 | `uv sync --frozen`과 lock 변경 검사, Actions SHA 고정, uv 버전 고정, Dockerfile digest, MinIO 소스 SHA256, Airflow constraints SHA를 release.json에 기록. |
| 17 | 측정 절차·원본 요약·재현 한계 | 4 | 범위 계산 재현 코드와 JSON 시행 6회가 md 중앙값과 일치. 한계: 재현에 로컬 PS_001 원본과 Git 이력 필요, 원본 artifacts는 Git 제외, 전체 처리·KPO 수치는 과거 버전 측정. |
| 18 | 처음 보는 사람의 README 동선 | 4 | 요약 → 5분 실행 → 데이터 의미 → 설계 → 근거/한계 → 구조 순서가 명확하고 docs 목차가 목적별 안내. 근거 표가 v0.5.0/0.5.1 과거 수치와 링크로 밀도가 높고, 빠른 실행의 첫 출력이 긴 JSON이라 URL 안내가 다소 묻힘. |
| 19 | 주장과 코드/근거 연결 | 5 | v0.5.3 변경 표의 각 주장을 테스트·코드로 대조해 일치 확인: 불량 시각 4건 추가, 범위 축소 3경우, 보간 불명 3경우, sentinel 비노출, Makefile 릴리스 대상 포함, MinIO SHA가 Dockerfile과 JSON에서 동일, 릴리스 JSON의 커밋이 구현 커밋과 일치. |
| 20 | 현재 상태·과거 증거·미완료 구분 | 4 | 대부분 "과거 근거"를 명시하고 미실행 항목을 따로 기록. `IMPLEMENTATION_STATUS.md` 5행과 19행은 v0.5.3 헤더 아래에서 v0.5.2·v0.5.0 근거를 "최신/현재"로 서술해 혼선(P5). |

영역 소계: 데이터 엔지니어링 23/25, 신뢰성 22/25, 아키텍처 18/20, 재현성 14/15, 전달력 13/15.

## 발견한 문제와 감점별 최소 개선

실행하지 않았으므로 모든 코드 지적은 **정적 추론**입니다. 문서 불일치는 읽기만으로 **확인**된 사항입니다. 보존 증거의 내부 일관성은 확인했고 외부 CI 링크·배포 상태는 검증 불가입니다.

- **P1 인버터 단위 분모 축소 미거부. 심각도 중간-낮음, 정적 추론, 미재현.** `pipeline.py:246-249`의 범위 축소 검사는 모든 인버터에 대해 `any()`로 날짜 겹침만 봅니다. 새 입력 버전에서 한 인버터가 통째로 빠져도 다른 인버터가 그 날을 덮으면 거부 없이 재게시되고 `expected_slots`가 줄어듭니다. 영향은 품질 비율이 조용히 개선된 것처럼 보일 수 있다는 점이며 freshness의 changed와 run 이력으로만 추적됩니다. 최소 개선은 둘 중 하나입니다. 기존 active 지표의 `expected_slots`보다 새 값이 작으면 `--restore`처럼 명시 플래그를 요구하거나, `data-contract.md` 41행에 "발전소 단위 검사이며 인버터 단위 소실은 거부하지 않음"을 명시합니다. 항목 3·4 감점 근거.
- **P2 전부 불명인 날의 일별 보간율 0.0 노출. 심각도 낮음, 정적 추론.** `metrics.py:49`는 불명 플래그를 분모에 포함해 0.0을 저장하고 `render.py:107-111`의 CSV와 metrics API가 그대로 내보냅니다. HTML 매크로와 `dashboard.js:71-77`만 "알 수 없음"으로 보정합니다. 같은 보고서 폴더의 HTML은 "불명을 0%로 표시하지 않는다"고 쓰지만 옆의 CSV는 0.0을 담습니다. 최소 개선은 CSV 안내 문단에 `interpolation_unknown_slots`와 함께 읽어야 한다는 한 줄을 추가하는 것입니다. 계산 버전 변경은 필요하지 않습니다. 항목 3 감점 근거.
- **P3 공개 replay 시 범위 계산 2회. 심각도 낮음, 정적 추론.** `replay.py:59`와 `pipeline.py:242`가 같은 파일에 대해 `source_bounds`를 각각 호출합니다. v0.5.3 파서 기준 PS_001 한 파일에 약 3.5초이므로 KPO 일별 task마다 약 7초가 추가됩니다. v0.5.0 병렬 측정은 과거 수치로 표기돼 있으나 이 추가 비용은 어디에도 없습니다. 최소 개선은 dry-run 계획 결과의 bounds를 ingest에 전달하거나 `bounds-reproduction.md`에 두 번 호출됨을 적는 것입니다. 항목 17 보조 근거.
- **P4 실패 기록 저장이 실패하면 원인 유실. 심각도 낮음, 정적 추론.** `pipeline.py:310-312`, `pipeline.py:507-508`, `ons.py:399-412`에서 예외 처리 중 DB 쓰기가 다시 실패하면 두 번째 예외가 전파되어 원래 코드가 남지 않습니다. CLI는 두 번째 예외의 코드만 출력합니다. 최소 개선은 실패 기록 호출을 try로 감싸고 원래 예외를 다시 올리는 것입니다. 항목 9 감점 근거.
- **P5 상태 문서의 버전 표기 혼선. 심각도 낮음, 확인된 문서 불일치.** `IMPLEMENTATION_STATUS.md` 5행은 "최신 경계 보완"으로 v0.5.2 근거를, 19행은 "배포·품질 관리" 현재 상태로 v0.5.0 검사 수를 가리킵니다. 헤더는 v0.5.3입니다. 최소 개선은 두 줄에 버전을 붙여 과거 근거로 표시하거나 v0.5.3 링크로 바꾸는 것입니다. 항목 20 감점 근거.
- **P6 실행 중 MinIO와 고정 빌드의 태그 동일. 심각도 낮음, 보존 증거의 명시된 한계.** `compose.yaml:43`과 `infra/k8s/services.yaml:94`는 `solarops-minio:2025-10-15`이고 digest 고정 검증은 `-pinned` 태그로만 수행됐습니다. JSON의 `live_storage_replaced: false`로 정직하게 기록돼 있어 결함이 아닙니다. 다음 재빌드 때 태그를 구분하거나 교체 사실을 기록하면 됩니다. 항목 14 감점 근거.
- **P7 자정 DST 전환 시간대의 날짜 경계. 심각도 낮음, 정적 추론, 현재 자료와 무관.** `metrics.py:7-10`의 `replace(tzinfo=zone)`은 자정에 전환하는 시간대에서 존재하지 않는 시각을 만들 수 있습니다. 기본 UTC와 2024년 이후 브라질에는 영향이 없고 뉴욕 02시 전환 테스트는 통과합니다. 필요하면 계약 문서에 한 줄로 한계를 적는 정도면 충분합니다. 감점 없음.

**보존 증거로 확인한 일관성.** `quality-v0.5.3.json`의 6회 시행 중앙값은 md의 0.674초·3.527초와 일치합니다. 범위 해시 6개가 동일합니다. MinIO 소스 SHA256이 Dockerfile·md·json에서 같습니다. 릴리스 JSON의 git_revision이 구현 커밋과 같고 compose·Helm·Makefile·pyproject가 모두 0.5.3입니다. 변경 표의 테스트 확장 주장은 각 테스트 파일에서 해당 케이스를 찾았습니다.

**검증하지 못한 것.** 테스트 통과 수, CI run 성공, Compose·kind 배포 상태, 브라우저 확인, 실제 PostgreSQL/MinIO 서비스 검사. 이들은 저장소 기록에 의존하며 본 평가가 재실행하지 않았습니다. 충분히 검사된 영역에 추가 영구 테스트나 스크립트를 권하지 않으며, 위 개선은 문서 한 줄 또는 작은 코드 수정 범위입니다.