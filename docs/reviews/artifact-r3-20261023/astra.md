# SolarOps Audit 산출물 독립 평가 — Astra R3

평가일: 2026-10-23 (Asia/Seoul). 평가 커밋: `36ac6ff937b06a481988d9264c65ac1a9597a59a`. 앱 `0.5.4`, 계산 `energy-interval-v2`. 릴리스의 구현 커밋은 `93ad341219de368068a22cb347ca74b8f43f6130`이며 평가 커밋과의 구현 경로 diff는 없었다.

**총점 96/100.** 공개·합성 자료를 다루는 로컬 배치 포트폴리오라는 범위에서 계약, 게시 원자성, 실패 보존, 계보와 설명이 잘 연결되어 있다. 이번 독립 실행에서 집중 검사 79개가 모두 통과했고, 새 합성 7일 데모에서도 실패 게시의 이전 결과 보존과 재처리 논리 해시 일치를 확인했다. 새로 확인한 수정 필수 결함은 없다. 이는 전체 코드·모든 시간대·현재 인프라의 무결성 보증을 의미하지 않는다.

평가 기준은 `docs/reviews/portfolio-rubric.md` v1의 고정 20항목이다. 면접, 개인 역량, 채용 가능성은 평가하지 않았다. 아래 5점은 해당 범위의 재현 가능한 계약·증거와 검토에서 확인된 미해결 결함이 없다는 뜻이며, 모든 상황을 전수 검사했다는 뜻은 아니다.

| # | 영역 / 고정 세부 항목 | 점수 | 근거와 판단 |
|---|---|---:|---|
| 1 | 데이터 — 출처/단위/시간 계약 | 5 | README와 `docs/data-contract.md`, `docs/ons-source-contract.md`가 BR의 W→추정 kWh와 ONS의 MWmed·미명시 시간대를 분리한다. `normalize/parquet.py:67`의 엄격한 UTC 파서와 ONS 원문 시각/null UTC 보존이 일치하며 offset·형식·그리드 검사를 직접 실행했다. 현장 실측 정확성을 주장하지 않는다. |
| 2 | 데이터 — 파싱·정규화·충돌 | 5 | metadata 중복 헤더/행 폭, canonical int64 인버터 ID, 중복 동일값 제거와 상이값 거부가 구현되어 있다. `raw_json`에 추가 컬럼을 보존하며 실제 캡처 raw를 처리한다. 관련 실패 입력과 원본 변경 경계 검사를 직접 통과했다. |
| 3 | 데이터 — 품질 분모·unknown·0 | 5 | `analytics/metrics.py:13`은 인버터별 관측 범위와 현지 일자의 교집합을 분모로 쓴다. 무효·누락·진짜 0, 보간 불명과 명시 False, DST 23/25시간·전체 누락일을 구분하는 기존 검사가 통과했다. 인버터 소실로 분모가 축소될 수 있다는 계약과 CSV/API 필드 동시 해석 조건도 명시되어 있다. |
| 4 | 데이터 — 증분/정정/철회 | 5 | ONS의 ETag/원본 SHA, 날짜 내용 hash, 월 cursor와 변경 manifest의 동일 트랜잭션, 사라진 날짜의 withdrawn이 구현되어 있고 정정·지연·철회·충돌·실패 보존을 직접 검사했다. BR은 선택 기간 upsert이고 날짜 철회는 지원하지 않는다는 제한을 정확히 구분한다. 실제 ONS 정정 도착을 관측했다는 과장도 없다. |
| 5 | 데이터 — 계보·결과 동등성 | 5 | 파일 SHA와 논리 hash의 목적이 다르며 source/version/run/규칙/metadata를 manifest에 남긴다. 캡처 raw 처리, 세 번 재처리, 시계열 변경의 hash 반영과 새 데모 7개 날짜의 동일성을 직접 확인했다. 공개 전체·환경 간 비교는 날짜 있는 과거 증거로 분리되어 있다. |
| 6 | 신뢰성 — 원자 게시·실패 보존 | 5 | `pipeline.py:323`의 객체 선저장→지표/active/metadata 트랜잭션과 ONS `commit()`이 코드에서 확인된다. before/during commit, 보고서 업로드/카탈로그 실패, 새 데모의 커밋 실패에서 이전 결과가 보존됐다. 일별 완료 경계와 배치 전체 원자성의 차이도 정확하다. |
| 7 | 신뢰성 — 동시성·재시도 | 5 | active 기대 run ID 조건부 갱신, 버전 claim, PostgreSQL advisory lock, 명시적 과거 복원, 오래된 보고서의 역순 완료 방지가 있다. SQLite에서 absent/existing/duplicate 경합과 승자 재시도를 실행했다. PostgreSQL 및 실제 KPO 재시도는 별도 역사 증거가 있으며 이번 실행으로 오인하지 않았다. |
| 8 | 신뢰성 — 조직/경로/비밀 경계 | 5 | active·조회·ONS cursor/partition/run과 객체 경로에 조직 범위가 적용되고 타 조직 보고서 접근이 거부된다. ZIP 경로/확장량, 읽기 API의 초기화 금지, 비밀 sentinel 비노출 검사가 통과했다. 로컬 관리 앱의 Host/Origin/CSRF와 허용 action, loopback 서비스 선언도 정적으로 확인했다. 고객 인증을 구현했다고 주장하지 않는다. |
| 9 | 신뢰성 — 진단·복구 절차 | 5 | 안전한 도메인 코드, 단계/실행 ID, BR 진단과 ONS 최근 시도/성공 cursor의 구별이 있다. `runtime.py:15`의 실패 기록 보호와 기존 검사가 2차 DB/파일 실패에도 원래 원인을 유지한다. 복구 문서는 running을 시간만으로 실패 처리하지 않고 실제 Pod/프로세스와 대조하도록 안내한다. 원본 행 번호 미제공은 명시된 제한이며 이 범위의 결함으로 새 기능을 요구하지 않는다. |
| 10 | 신뢰성 — 회귀 검사의 의미와 실제 실행 | 5 | 단순 정상 출력 외에 golden 2.0kWh, 잘못된 시간/ID, 충돌, 누락/DST, 원본 변경, 경합, 실패 게시와 2차 진단 실패를 검증한다. 지정된 5개 파일을 1회 실행해 **79통과·0제외·24.60초**. v0.5.4 전체 140통과/14제외와 실제 서비스13통과는 작성자의 역사 증거로 별도 취급한다. |
| 11 | 아키텍처 — 역할·공통 CLI | 5 | `cli.py`, `replay.py`, `dags/solarops_factory.py`가 로컬 subprocess와 KPO에서 같은 CLI를 호출한다. 분석·정규화·저장·보고서·읽기 모델의 책임이 분리되고 DAG에 계산 로직을 복제하지 않는다. LocalExecutor와 KPO, 앱 DB와 Airflow DB의 역할 설명도 코드와 맞는다. |
| 12 | 아키텍처 — 저장/조회 모델과 제약 | 4 | 조직/발전소/일자/시간대/계산 버전 PK와 단일 SELECT snapshot, DB 읽기 전용, 필요한 필드만 고르는 월별 overview, 이력 SQL pagination/index가 적절하다. 다만 발전소 metrics/issues는 전체 선택 결과를 읽고 Python에서 페이지를 자르며(`api/app.py:177,196`), 모든 조회가 같은 비용 경계를 갖지는 않는다. 현재 크기의 결함이나 실패를 재현한 것은 아니며 대표 경로의 검증과 명시된 규모 한계 수준으로 평가했다. |
| 13 | 아키텍처 — 기술 선택·비용·대안 | 5 | `technology-stack.md`는 DuckDB 한도와 전체 RSS의 차이, Python 비용, 일별 작은 파일, JSON 조회, Pod 기동 비용, Airflow 운영 부담을 설명한다. Spark/Kafka 미도입과 정적 UI 선택을 요구·규모에 연결하고 직접 비교하지 않은 대안의 우월성을 주장하지 않는다. CPU 증가를 함께 제시한 KPO 측정도 좋다. |
| 14 | 아키텍처 — 배포 버전·설정과 운영 경계 | 5 | 단일 release 명세, 선언 검사, 구현 SHA와 worker/Airflow image ID가 연결된다. **release check 0.5.4 통과**. Compose/kind/네이티브 독립 저장소, 중지된 Compose Airflow, 과거 KPO 증거, 읽기 UI와 별도 관리 서버의 경계를 문서가 구분한다. 이번 검토에서 live 배포 상태를 조회하지 않았다는 한계는 남긴다. |
| 15 | 재현성 — 새 환경의 작은 오프라인 시연 | 4 | 새 출력 폴더에서 공개 자료나 Docker 없이 합성 정상 처리→커밋 실패→복구→보고서가 실제로 완료됐다. 출력 경로 재사용 거부와 명시적 SQLite/S3 미사용 설정도 좋다. 다만 이번 독립 실행은 기존 Python 3.12.13 venv를 사용했으며 새 가상환경의 frozen 설치·wheel 설치를 재실행하지 않았다. 새 환경 근거는 Windows/Ubuntu CI의 기록과 정의에 의존한다. |
| 16 | 재현성 — 의존성·실행 버전/이미지 추적 | 4 | 앱 의존성 uv.lock, Docker 기반 digest, MinIO archive SHA/base digest, Airflow constraints SHA, 릴리스 이미지 ID가 있다. PostgreSQL 서비스 선언은 digest 없는 버전 태그(`compose.yaml:37,70`)이고 Airflow constraints는 wheel hash 잠금이 아니다. 캐시 없는 독립 MinIO 재빌드도 미검증이라고 정확히 적었다. 실행 식별은 강하지만 전체 인프라를 같은 바이트로 다시 만드는 보장까지는 없다. |
| 17 | 재현성 — 측정 절차·원본 요약·재현 한계 | 4 | benchmark 문서/JSON에 표본·횟수·동시성·순서·hash·자원·기준·한계가 있으며 bounds 재현 문서는 과거 함수와 현재 함수의 3회 교차 측정 코드를 제공한다. 반면 일부 부하 probe/원시 지연/EXPLAIN은 Git 제외 로컬 artifacts에만 있어 새 checkout에서 요약 p95를 독립 재계산하기 어렵다(`technical-20261023.md:53`). 과거 수치를 현재 성능으로 포장한 문제는 발견하지 않았다. |
| 18 | 전달력 — 처음 보는 사람의 README 동선 | 5 | 문제→독립 합성 5분 재현→수치 의미→구조→실행 근거→한계 순으로 연결된다. 비공개 clone 권한, 최초 설치 네트워크, 실행 PC의 loopback URL, 종료 방법과 보존되는 결과를 알려준다. 한 쪽 요약과 데모 안내가 별도로 있어 상세 문서의 양을 조절할 수 있다. |
| 19 | 전달력 — 주장과 코드/근거 연결 | 5 | README/사례/계약/아키텍처에서 실제 코드·테스트·날짜별 benchmark·release JSON으로 이동할 수 있다. 51개 전체와 4월5개, 1,440만 행과 작은 합성, 원본 보간과 유효값, 추정 에너지와 검토 후보를 구별한다. 이번 검토에서 확인한 핵심 주장과 구현이 일치했다. |
| 20 | 전달력 — 현재 상태·과거 증거·미완료 항목 구분 | 5 | 0.5.4 검사/배포 기록과 0.5.0 KPO 측정, 전체 처리 역사, 최신 파서의 추가 비용을 명시적으로 구별한다. 단일 호스트, 외부 SLO/고객 인증/현장 고장 정답·다중 호스트 복구 미검증을 완료 실적으로 세지 않는다. blind 범위에 따라 handoff/plan은 읽지 않았으며 그 문서의 정확성을 평가했다고 주장하지 않는다. |

영역 합계: 데이터 25/25, 신뢰성 25/25, 아키텍처 19/20, 재현성 12/15, 전달력 15/15 = **96/100**.

## 직접 실행한 확인

1. `.venv/Scripts/python.exe -m pytest tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py -q --basetemp artifacts/astra-r3-pytest-20261023 --junitxml artifacts/artifact-review-r3-20261023/astra-pytest.xml` — 79통과, 실패/오류/제외 0, 24.60초. 최초 지시의 존재하지 않는 `test_energy_v2.py`는 메인 평가 조정자의 승인으로 실제 `test_calculation_v2.py`로 정정했다.
2. `.venv/Scripts/python.exe scripts/demo/portfolio_demo.py --output artifacts/astra-r3-synthetic-20261023` — 7개 active, `failed_publish_kept_active_data=true`, `replay_hashes_identical=true`, batch committed2/failed1. 보고서 `23657762-027a-468e-af99-1a216f69160d`, `partial_period`로 정확히 표시.
3. `.venv/Scripts/python.exe scripts/release/release.py check` — `Release declarations aligned: 0.5.4`.
4. `git rev-parse HEAD`, 구현 커밋과 평가 커밋의 지정 구현 경로 diff, Python 버전 확인. Python 3.12.13. 구현 diff 없음.

로그는 이 폴더의 `astra-pytest.txt/xml`, `astra-demo.txt`, `astra-release.txt`에, 실제 합성 산출물은 `../astra-r3-synthetic-20261023/`에 보존했다. 전체 회귀, 새 의존성 설치, 브라우저, 서비스/컨테이너 시작·중지, 외부 네트워크, 공개 원본 재처리, 새로운 영구 테스트는 수행하지 않았다.

## 확인된 결함과 제한의 구분

이번 검토에서 재현한 새 제품 결함은 **0건**이다. 위 4점 항목은 증거의 휴대성·재현 범위 또는 알려진 비용 경계에 대한 평가이며 데이터 손상이나 운영 장애가 발생했다는 뜻이 아니다.

- **조회 비용의 경계:** 전체 읽기 후 pagination은 정적 확인이다. 현재 월별/발전소 규모에서 실패를 확인하지 않았으므로 즉시 새 저장 계층이나 분산 기술을 요구하지 않는다. 최소 개선은 해당 API의 limit가 응답 크기 제한임을 문서화하는 것이며, 데이터가 늘어 실제 병목이 확인되면 기존 쿼리에 SQL pagination을 적용할 수 있다.
- **빌드 재현:** PostgreSQL 버전 태그는 정적으로 확인했다. 실제 태그 변경이나 공급망 문제를 관측하지 않았다. 향후 같은 바이트의 환경 재구성을 목표로 할 때 선언에 확인한 digest를 병기하는 작은 개선이면 충분하다. 현재 wheel hash 미강제/MinIO 캐시 사용 한계 설명은 정확하다.
- **측정 증거 전달:** 원시 부하 자료가 Git 제외 경로에 있다는 사실은 문서의 진술이며 이번에 그 원본을 읽거나 p95를 재계산하지 않았다. 필요하면 비밀·원본 데이터 없는 작은 재현 코드와 표본/집계 절차를 날짜 문서에 보존하면 된다. 상시 부하 테스트나 새 영구 검증 도구를 요구하지 않는다.

이미 문서화한 BR 개별 인버터 소실 시 분모 감소, 날짜 철회 미지원, 보간 비중과 unknown 수의 공동 해석, 자정 전환을 포함한 모든 IANA 시간대 미검증, 원본 행 번호 미제공, ONS 최근20시도/외부 로그 대조는 수용한 범위다. 설비 가동기간이나 현장 고장 정답을 새로 만들어 채울 근거가 없으며 이를 숨기지 않고 계약에 설명했다. 임의 시간대·고객 운영으로 범위를 넓힐 때 재검토할 조건이다.

이번 평가에서는 화면을 직접 조작하거나 시각 QA하지 않았다. UI 관련 전달력은 README·문서·API 계약의 검토 결과이며 과거 스크린샷/접근성 기록을 이번 직접 브라우저 검사로 세지 않는다. 자세한 읽기 범위와 모델 지정 정보는 `astra-provenance.md`에 기록했다.
