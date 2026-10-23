File count reconciles to the 303 tracked files once the 50 bytecode cache files my test run created are excluded. Review complete; the evaluation follows.

## SolarOps Audit 산출물 독립 평가 (Fable, R5)

평가 모델 Claude Fable 5.1 (claude-fable-5-1). 대상 커밋 faa6f3baf8e1925ccc21f402419cf1333f2e5010, 앱 0.5.6, 구현 4b9959e. 읽은 범위는 H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-fable 내부와 지정된 service-probe.py 하나뿐입니다. 원본 저장소, 다른 평가, 이전 점수는 읽지 않았습니다. 기준은 docs/reviews/portfolio-rubric.md v1 (20항목, 각 0~5점)입니다.

**총점 94 / 100**

| 영역 | 항목 | 점수 | 근거 요약 |
|---|---|---:|---|
| 데이터 엔지니어링 | 1 출처/단위/시간 계약 | 5 | data-contract.md, ons-source-contract.md, data-sources.md의 계약이 timestamp_utc(normalize/parquet.py:67-89), ONS CONTRACT(ons.py:38-51)와 일치. MWmed·ts_utc=null 보존을 서비스 검사와 직접 확인 |
| | 2 파싱·정규화·충돌 | 5 | DuckDB 외부 정렬, 인버터 ID 정규화, 동일/상이 중복 구분(pipeline.py:84-94), metadata 모호 컬럼 거부, ZIP 경로 이탈 차단을 test_contracts/test_integrity_boundaries 실행으로 확인 |
| | 3 품질 분모·unknown·0 | 4 | 인버터별 원본 범위 분모, 무효 슬롯 null, 보간 불명 구분을 코드와 합성 시간대 probe로 확인. 단 발견 1(과거 지표 행의 키 부재 시 보고서 생성 실패) |
| | 4 증분/정정/철회 | 4 | ONS ETag·cursor·withdrawn·충돌을 SQLite와 격리 PostgreSQL에서 실행 확인. BR의 SOURCE_RANGE_SHRINK·--restore 확인. 실제 원천 정정 도착은 fixture 검증뿐이며 2개월 밖 정정은 수동 월 지정이 필요하다고 문서가 명시 |
| | 5 계보·결과 동등성 | 5 | 데모 7일 Parquet에서 kWh를 독립 재계산해 지표와 전부 일치. 같은 바이트·다른 라벨에서 지표 동일·논리 hash 상이(문서 계약대로). series/보고서 SHA 조회 검증 코드 확인 |
| 신뢰성 | 6 원자 게시·실패 보존 | 5 | 데모 실패 주입 후 이전 active 유지·재처리 hash 일치. PG/MinIO 격리 검사 13개 통과(before/during commit, 보고서 upload/catalog 실패) |
| | 7 동시성·재시도 | 5 | 조건부 active 교체(pipeline.py:463-477), advisory lock, 버전 claim 경합, 보고서 역순 완료, ONS cursor 충돌을 SQLite·PG 양쪽 실행으로 확인 |
| | 8 조직/경로/비밀 경계 | 5 | 모든 조회에 org 조건, identifier/경로 검증, 오류 코드 허용 목록(brpvgen.py:46-64)과 sentinel 비노출 검사, 관리 서버 Host/Origin/토큰 검사(admin/app.py:29-63), loopback 포트, .env 생성·패키징 거부 확인 |
| | 9 진단·복구 절차 | 4 | inspect-runs가 SELECT만 실행함을 검사로 확인, recovery.md 코드별 절차, SQLite 복원 드릴 직접 실행. PostgreSQL/MinIO 복원과 KPO 재시도는 과거 기록만 |
| | 10 회귀 검사의 의미와 실행 | 5 | 154개 중 140 통과·14 제외를 직접 실행. 제외 13개는 서비스 opt-in이며 격리 컨테이너에서 별도 13 통과. 검사 내용이 장애 주입·경합·조직 격리 등 실제 실패를 잡는 구성 |
| 아키텍처 | 11 역할·공통 CLI | 5 | cli.py 하나를 네이티브·Compose subprocess·KPO가 호출(dags/solarops_factory.py:21-122). DAG에 계산 복제 없음 |
| | 12 저장/조회 모델과 제약 | 4 | PK·active 포인터·읽기 전용 Catalog·단일 SELECT overview 확인. 발견 2(migrations SQL이 모델과 불일치) |
| | 13 기술 선택·비용·대안 | 5 | technology-stack.md가 버전·대안·재검토 조건을 표로 제시, ADR 0001~0008과 일치 |
| | 14 배포 버전·설정·운영 경계 | 5 | release.py check 통과, Dockerfile digest 고정, releases/0.5.6.json 이미지 ID, 환경별 저장소 독립과 관리 서버 범위 문서화 |
| 재현성 | 15 새 환경 오프라인 시연 | 5 | 새 .venv를 오프라인 캐시로 생성 후 portfolio_demo 성공. 결과 832.424 kWh가 문서 수치와 일치 |
| | 16 의존성·실행 버전/이미지 추적 | 5 | uv.lock frozen 동기화 성공, 기반 이미지 digest, MinIO 소스 SHA 고정, 이미지 이력 JSON. Airflow 전이 의존성은 hash 잠금이 아님을 명시 |
| | 17 측정 절차·원본 요약·재현 한계 | 4 | 조건·산식·표본(evidence/technical-20261023)·재현 코드(bounds-reproduction) 보존. 공개 자료·kind 측정은 이 export에서 재현 불가 |
| 전달력 | 18 처음 보는 사람의 README 동선 | 4 | 빠른 실행 명령이 그대로 동작. 다만 본문이 버전별 수치·연속성 문서 링크에 많이 의존하고, 대표 화면 수치(74.9%, 17%)는 공개 자료 없이 확인 불가 |
| | 19 주장과 코드/근거 연결 | 5 | DESIGN_QUESTIONS·CASE_STUDY가 파일·검사·벤치마크로 연결. 제가 확인한 수치(검사 수, 데모 kWh, 제외 수)가 문서와 일치 |
| | 20 현재 상태·과거 증거·미완료 구분 | 5 | 벤치마크마다 버전·커밋을 표기하고 "과거 근거"를 반복 구분. IMPLEMENTATION_STATUS가 완료/미실행을 분리 |

**강점(직접 확인)**

- 데모 7개 파티션의 Parquet 유효값 합×0.25가 저장 지표와 모두 일치했고, 누락 2·보간 2/192·검토 후보 1이 fixtures.py의 주입 위치와 정확히 대응합니다.
- America/Sao_Paulo 시간대로 같은 fixture를 처리하면 8개 현지 날짜, 기대 1,344·관측 1,342·누락 2, 첫날 24·마지막날 168 슬롯, 총 kWh가 UTC와 동일했습니다. 분모 계약이 시간대 경계에서 유지됩니다.
- v0.5.6의 핵심 주장(warning_count는 분석 규칙만, quality_issue_count는 입력 중복 포함)이 데모 CSV에서 4월 1일 0/1로 확인됐습니다.
- 모든 실패 기록이 허용 코드만 남기고, 실패 기록 자체의 2차 오류도 원래 예외를 덮지 않는 검사가 실제로 통과했습니다.
- 관리 서버는 데이터 API를 노출하지 않고 원격 클라이언트·잘못된 Host/Origin·토큰 없음을 403으로 거부합니다.

**발견과 최소 개선안**

1. src/solarops/reports/render.py:63 (build_report). 계산 v2 지표 행에 interpolation_unknown_slots 키가 없으면 KeyError로 월간 보고서 생성이 실패합니다(CLI에서는 BR_UNEXPECTED_ERROR로 분류). 같은 파일 43~45행은 source_inverter_bounds 부재를 null로 처리하고, api/readmodels.py:31은 .get을 쓰므로 overview/API는 정상입니다. 상태: 합성 DB에서 키를 제거해 재현. 과거 공개 v2 행에 실제로 키가 없는지는 이 export로 판단할 수 없으며, 문서상 hash 동등성 주장으로 보아 키는 0.5.2 이전부터 존재했을 가능성이 큽니다. 영향: 낮음·조건부. 최소 개선: metric.get으로 읽고 부재 시 해당 일을 "알 수 없음"으로 집계하거나, 데이터 계약에 "v2 지표는 항상 이 키를 가진다"를 명시.
2. migrations/0001_catalog.sql. 헤더는 "Generated from solarops.storage.postgres"지만 collection_cursor·collection_partition·collection_run(postgres.py:82-84)과 PostgreSQL 인덱스 2개(postgres.py:53-65)가 없습니다. 상태: 정적 비교. 영향: 낮음. db-migrate가 실제 경로이고 ons-source-contract.md:30이 이를 요구하므로 동작 결함은 아니지만 문서 산출물이 모델과 어긋납니다. 최소 개선: SQL 재생성 또는 헤더에 "ONS 테이블·인덱스는 db-migrate로만 생성"을 명기.
3. 계약 관찰(결함 아님). api/readmodels.py:53은 첫 source object로 자료 종류를 필터하고 storage/postgres.py:195는 전부 일치를 요구합니다. data-contract.md:51과 ADR 0006이 같은 ingest의 source_kind 동일 계약으로 설명하므로 일관됩니다.
4. 전달 관찰(결함 아님). 638개 로컬 링크 중 깨진 링크는 handoff.md, plan.md, docs/plan/, docs/reviews/*, docs/worklog/* 등 의도적으로 제외된 파일로만 향하며 전체 저장소에는 존재한다고 안내받았습니다.

**실행한 명령과 결과**

| 명령 | 결과 |
|---|---|
| uv sync --frozen --offline --python (공유 3.12) | 새 .venv, 42개 패키지, 오프라인 캐시로 충분 |
| import solarops 경로 확인 | 이 export의 src/solarops/__init__.py, SOLAROPS_BUILD_REVISION=faa6f3b… |
| pytest --junitxml=artifacts/fable-tests.xml | 140 통과·14 제외·0 실패, 41.41초 (제외: 서비스 opt-in 13, 호스트 symlink 권한 1) |
| scripts/demo/portfolio_demo.py --output artifacts/fable-demo | 활성 7, 실패 게시 보존 true, 재처리 hash 동일, 보고서 partial_period, 832.424 kWh |
| scripts/validation/backup_restore_drill.py --output artifacts/fable-restore | 34파일 SHA 검증, integrity ok, 손상 사본 거부, 복원 API·과거 보고서·raw 재처리 hash 일치 |
| scripts/release/release.py check | Release declarations aligned: 0.5.6 |
| service-probe.py artifacts/fable-services | 격리 PostgreSQL 16.10·pinned MinIO에서 13 통과, 27.14초, 컨테이너 2개 중지·보존 |
| python -c 소형 probe (artifacts/fable-probe) | Parquet 재계산 일치 7/7, Sao Paulo 분모 확인, 라벨 포함 hash 확인, 과거 지표 키 부재 KeyError 재현, 링크 638개 스캔, 추적 파일 303개 재확인 |

**검토한 경로**: README.md, AGENTS.md, CHANGELOG.md, CONTRIBUTING.md, PRODUCT.md, pyproject.toml, Makefile, .env.example, src/solarops 전체(pipeline, normalize, analytics, contracts, storage, acquisition, reports, api/app·readmodels, admin, diagnostics, replay, cli, config, runtime, fixtures, release.json, monthly.html), tests 13개 파일, dags/solarops_factory.py·ons_daily.py, infra(compose, Dockerfile 2종, k8s/services.yaml, helm values), migrations, scripts(demo, release, validation의 drill·check_docs·validate_dags·package_source, data/full_dataset, ops/bootstrap), .github/workflows 2개, docs(README, IMPLEMENTATION_STATUS, data-contract, ons-source-contract, data-sources, architecture 2, adr 8, guides 2, runbooks 4, portfolio 4, benchmarks 15개와 evidence, releases/0.5.6.json, image-versions.json, worklog/bounds-reproduction, reviews/portfolio-rubric).

**한계**

- ruff와 scripts/validation/check_docs.py는 실행 환경이 거부해 직접 실행하지 못했습니다. 문서의 통과 주장은 미검증이며, 대신 제 링크 스캔으로 깨진 링크가 제외 파일로만 향함을 확인했습니다.
- symlink 경로 이탈 검사 1개는 호스트 권한으로 제외됐습니다. CI 통과 주장은 과거 기록입니다.
- 공개 BR-PVGen 51개 처리, ONS 실제 수집, kind/KPO 병렬 측정, PostgreSQL/MinIO 복원 드릴, 브라우저 검증은 이 export에서 재현하지 않았으며 모두 문서상 역사 근거로만 취급했습니다.
- 아카이브 SHA256은 아카이브 파일이 없어 확인하지 못했고, 추적 파일 303개는 디렉터리 집계로만 대조했습니다. 제 검사 실행으로 src/tests/scripts/dags 아래 __pycache__ 50개와 artifacts/ 하위 산출물이 생겼으며 소스 파일은 수정하지 않았습니다.
- 발견 1의 실제 영향은 과거 v2 지표 행의 키 존재 여부에 달려 있으며 원본 저장소 확인이 필요합니다.