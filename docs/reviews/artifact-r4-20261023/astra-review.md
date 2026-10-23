# SolarOps Audit 독립 산출물 평가 — Astra R4

평가일: 2026-10-23 Asia/Seoul. **90/100점**. 공개/합성 자료의 로컬 배치 파이프라인이라는 고정 범위에서 평가했다. 면접·개인 역량·채용 가능성·상용 운영 적합성은 평가하지 않았다. 높은 점수와 별개로 아래의 재현된 보고서 활성 키 충돌은 수정할 가치가 있는 미해결 결함이다.

대상 커밋은 `954a421af31c34d14be99f0354ab783e4d18dec7`, 앱은 `0.5.5`, 구현 릴리스 커밋은 `cedf70216add558956001140c56b6931c40a1198`이다. 평가 규칙은 `docs/reviews/portfolio-rubric.md:7–22`의 고정 20항목, 각 0–5점이다. 아래 파일 위치는 모두 읽기 전용으로 제공된 `H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/source/` 기준이다. 원본 작업 저장소·다른 평가·이전 점수는 읽지 않았다. 제외된 연속성 문서의 링크는 결함으로 계산하지 않았다.

## 점수표

| 영역 | 고정 세부 항목 | 점수 / 5 | 구체 근거와 판단 |
|---|---|---:|---|
| 데이터 엔지니어링 | 출처/단위/시간 계약 | 5 | `docs/data-contract.md:13–31`, `docs/ons-source-contract.md:7–20`, `src/solarops/normalize/parquet.py:67–89`, `src/solarops/acquisition/ons.py:38–50,151–207`. W·MWmed·시각 불명·추정 kWh를 분리하며 UTC/오프셋/그리드 검사를 직접 통과했다. 현장 계측 정확도는 주장하지 않는다. |
| 데이터 엔지니어링 | 파싱·정규화·충돌 | 5 | `contracts/brpvgen.py:67–90`(정확한 위치는 `src/solarops/contracts/brpvgen.py`), `src/solarops/normalize/parquet.py:22–29,92–147`, `src/solarops/pipeline.py:84–94`. 헤더/폭/ID/중복 충돌, 보간·표본 수·추가 컬럼 보존을 기존 계약 검사로 직접 확인했다. |
| 데이터 엔지니어링 | 품질 분모·unknown·0 | 4 | `src/solarops/analytics/metrics.py:24–51,111–146`, `src/solarops/reports/render.py:57–90`, `tests/test_calculation_v2.py:22–124`. 유효한 0, 무효 null, DST 누락일, 보간 불명이 구분된다. 분모가 원본 관측에 종속되므로 인버터 소실로 작아질 수 있으며 작은 입력에서 재현했다. 문서가 이 한계를 명시한다. |
| 데이터 엔지니어링 | 증분/정정/철회 | 4 | `src/solarops/acquisition/ons.py:248–342,377–399`, `src/solarops/pipeline.py:175–249`, `tests/test_publication_boundaries.py:202,257`. ONS 정정·날짜 철회·동일 응답·실패 cursor는 SQLite와 실제 PostgreSQL에서 통과. BR은 일자 범위 축소를 차단하지만 인버터 단위 소실은 운영자 판단에 남아 있다. BR의 전체 철회 기능을 요구해 감점한 것은 아니다. |
| 데이터 엔지니어링 | 계보·결과 동등성 | 5 | `src/solarops/pipeline.py:129–174,395–445`, `src/solarops/normalize/parquet.py:124–147`, `src/solarops/reports/render.py:33–45,60–98`. raw SHA, 원본 추가 필드, 계산 버전, 실행 식별자, 인버터 범위가 연결된다. 7일 재처리의 논리 해시 일치·실패 전후 보존·보고서 계보를 직접 확인. 전체 공개 자료 동등성은 역사 증거로만 취급했다. |
| 신뢰성 | 원자 게시·실패 보존 | 5 | `src/solarops/storage/minio.py:42–73`, `src/solarops/pipeline.py:454–502`, `src/solarops/reports/render.py:124–156`, `src/solarops/acquisition/ons.py:299–342`. 원본 캡처, 일별 결과, 보고서 객체/DB 실패, ONS cursor 트랜잭션을 직접 검사했다. 다일 배치의 일부 완료를 전체 원자성으로 오해하지 않게 문서화했다. 보고서 선택 키의 별도 결함은 저장/조회 모델 항목에 반영했다. |
| 신뢰성 | 동시성·재시도 | 5 | `src/solarops/storage/postgres.py:107–119`, `src/solarops/pipeline.py:463–485`, `tests/test_services.py:86–146`, `dags/solarops_factory.py:145 이후`. 동일 버전 경쟁·기대 active 비교·오래된 보고서의 역순 완료 방어를 SQLite와 실제 PostgreSQL에서 통과. 실제 KPO 재시도는 이번 재실행 없이 역사 근거로 구별했다. |
| 신뢰성 | 조직/경로/비밀 경계 | 4 | `src/solarops/config.py:13–16`, `src/solarops/storage/postgres.py:159–175`, `src/solarops/api/app.py:67–94,242–258,322–335`, `src/solarops/admin/app.py:29–60`. 조직별 조회, 경로 제한, 읽기 전용 DB, 안전 오류 코드의 대표 검사는 통과. admin의 Host/Origin/CSRF·허용 명령은 정적 검토만 했으므로 전체 보안 경계를 직접 재검증했다고 볼 수 없다. 로컬 범위에 없는 고객 인증 부재는 감점 사유가 아니다. |
| 신뢰성 | 진단·복구 절차 | 4 | `docs/runbooks/recovery.md:5 이후`, `src/solarops/diagnostics.py:12–185`, `docs/runbooks/backup-restore.md:7 이후`. 실패 기록 자체의 실패와 running 잔류까지 설명하고 안전 코드·계보·재시도 관계를 검사한다. 백업/복원은 상세 절차와 역사 증거가 있으나 이번 실행에서 독립 복원하지 않았다. |
| 신뢰성 | 회귀 검사의 의미와 실제 실행 | 5 | `tests/test_contracts.py`, `tests/test_pipeline.py`, `tests/test_calculation_v2.py`, `tests/test_publication_boundaries.py`, `tests/test_integrity_boundaries.py`, `tests/test_services.py`. 단순 성공 확인을 넘어 충돌·변조·업로드/DB 실패·역순 게시·조직 격리·DST를 다룬다. 79개 핵심 오프라인 + 13개 실제 서비스 검사가 직접 통과했다. 전 테스트를 실행한 것으로 쓰지 않는다. |
| 아키텍처 | 역할·공통 CLI | 5 | `src/solarops/cli.py:27 이후`, `dags/solarops_factory.py:22–129`, `docs/architecture/system.md:66–86`. 계산·저장·조회·일정이 나뉘고 LocalExecutor와 KPO 모두 같은 CLI를 실행한다. API는 읽기 전용이며 변환 작업을 시작하지 않는다. |
| 아키텍처 | 저장/조회 모델과 제약 | 3 | `src/solarops/storage/postgres.py:66–84,159–197`, `src/solarops/reports/render.py:64,142–155`. 활성 포인터/불변 이력과 일관된 SELECT는 적절하다. 그러나 유효한 발전소 ID `all`과 전체 범위를 같은 문자열 키로 저장하는 충돌을 직접 재현했다. 행 수준 PK/선택 범위 계약의 실제 공백이다. |
| 아키텍처 | 기술 선택·비용·대안 | 5 | `docs/architecture/technology-stack.md:9 이후`, `docs/adr/0008-storage-integrity.md:9 이후`. DuckDB 제한·일별 파일·JSON 조회 비용·SQLite/PG 차이·Airflow 기동 비용·MinIO 자체 빌드 부담을 설명한다. Kafka/Spark 등을 추가하지 않은 판단도 배치 규모에 맞고 비교 실측 부재를 숨기지 않는다. |
| 아키텍처 | 배포 버전·설정과 운영 경계 | 4 | `src/solarops/release.json`, `scripts/release/release.py:16–64`, `docs/releases/0.5.5.json:2–20`, `infra/docker/Dockerfile:1–29`. release check 0.5.5 직접 통과. 커밋/이미지 ID와 Compose/kind 분리가 명시된다. 이번에는 Airflow/Kubernetes 배포·실제 앱 이미지 실행을 재검증하지 않았고 선언은 가변 태그를 사용한다. |
| 재현성 | 새 환경의 작은 오프라인 시연 | 4 | `README.md:13–36`, `scripts/demo/portfolio_demo.py:1–101`, `.github/workflows/ci.yaml:17–36`. 합성 7일 시연은 새 출력 폴더에서 직접 성공했고 실패/재처리를 스스로 검증한다. 기존 Python 3.12 환경을 사용했으므로 깨끗한 머신의 최초 의존성 설치까지 독립 재현한 것은 아니다. |
| 재현성 | 의존성·실행 버전/이미지 추적 | 4 | `pyproject.toml:5–37`, `uv.lock`, `infra/docker/Dockerfile:1–29`, `infra/docker/Dockerfile.minio:2–12`, `docs/releases/0.5.5.json`. Python 범위·직접/전이 의존성·기반 digest·MinIO 소스 SHA·Airflow constraints가 추적된다. 격리 서비스 실제 이미지 ID를 확인했다. 캐시 없는 이미지/바이너리 재현 빌드는 수행하지 않았으며 문서도 그 한계를 명시한다. |
| 재현성 | 측정 절차·원본 요약·재현 한계 | 4 | `docs/benchmarks/technical-20261023.md:27–53`, `docs/benchmarks/incremental-v0.5.0.md:21–45`, `docs/worklog/2026-10-23-bounds-reproduction.md:5 이후`. 표본 수·순서·워밍업·CPU/메모리·캐시·단일 호스트 한계와 JSON 요약이 있다. 일부 원시 지연/EXPLAIN/일회 probe는 로컬 Git 제외 아티팩트에만 있어 제공 스냅샷만으로 모든 수치를 다시 계산할 수 없다. |
| 전달력 | 처음 보는 사람의 README 동선 | 5 | `README.md:3–36,38–60,91 이후`. 문제·시연·자료 의미·구조·근거로 연결되고 Docker/전체 다운로드 없는 첫 경로가 실제 동작했다. 과도한 환경 구축을 첫 단계로 강제하지 않는다. |
| 전달력 | 주장과 코드/근거 연결 | 5 | `README.md:38–108`, `docs/data-contract.md`, `docs/architecture/system.md:145 이후`, `docs/benchmarks/stack-authenticity-20261023.md`. 출처·정량 결과·코드·버전별 근거를 찾기 쉽고 추정 에너지/검토 후보/운영 실적을 구별한다. 전체 역사 수치를 이번 검사의 결과로 둔갑시키지 않는다. |
| 전달력 | 현재 상태·과거 증거·미완료 구분 | 5 | `README.md:91–108,130 이후`, `docs/IMPLEMENTATION_STATUS.md:3–9,65 이후`, `docs/benchmarks/quality-v0.5.5.md:3–16`. 최신 구현·배포 기록과 과거 공개 전체/KPO/화면 근거의 버전 차이를 표시하고 고객/외부 운영 미검증을 명시한다. blind 범위상 현재 plan/handoff 자체의 정확성은 평가하지 않았다. |

영역 합계: 데이터 엔지니어링 **23/25**, 신뢰성 **23/25**, 아키텍처 **17/20**, 재현성 **12/15**, 전달력 **15/15**. 총 **90/100**.

## 직접 실행한 검사

- Python `3.12.13`; `solarops.__file__`이 제공 스냅샷의 `source/src/solarops/__init__.py`로 해석됨을 가장 먼저 확인했다.
- 지정된 핵심 5개 파일: **79 passed, 34.08s**. `source/artifacts/astra-r4-pytest.xml` 보존.
- 허용된 격리 서비스 driver: **13 passed, 22.56s**. `source/artifacts/astra-r4-services/services-fixed.xml` 및 runtime JSON 보존. 새 PostgreSQL/MinIO 컨테이너만 사용했고 두 컨테이너의 `exited` 상태를 별도 확인했다. 삭제하지 않았다.
- `portfolio_demo.py --output artifacts/astra-r4-synthetic`: 활성 7개, 실패 전후 active 보존, 재처리 해시 일치, committed 배치 2개/failed 1개, `partial_period` 월간 HTML·CSV·manifest 생성. `source/artifacts/astra-r4-synthetic/evidence.json`에 결과 보존.
- `scripts/release/release.py check`: `Release declarations aligned: 0.5.5`.
- `source/artifacts/astra-r4-probe.py`: 신규 합성 자료만 사용해 아래 2가지 경계 확인. 결과는 `source/artifacts/astra-r4-probes/result.json`.

첫 pytest 시도는 `source/artifacts`가 아직 없어서 지정 basetemp 생성이 실패했다(26 passed, 53 setup errors, 2.09s). 제품 실패가 아니라 평가자의 실행 준비 오류다. 최초 JUnit을 `astra-r4-pytest-initial-setup-error.xml`로 보존하고 JUnit 작성 과정에서 생긴 상위 출력 폴더 아래로 동일 명령을 재실행했다. 성공 결과만 남기는 방식으로 숨기지 않았다.

## 발견 사항과 최소 개선

### F1 — 서로 다른 보고서 선택이 같은 active 키를 사용함: 재현된 결함, 중간 영향

위치: `src/solarops/reports/render.py:64,142–155`; `src/solarops/storage/postgres.py:75–79`; `src/solarops/config.py:13–16`; `src/solarops/api/app.py:272–320`.

식별자 계약은 `all`을 허용한다. `all`과 `OTHER`라는 합성 발전소를 적재하고, `build_report(settings, '2024-04', 'all')` 뒤에 `build_report(settings, '2024-04')`를 실행했다. 개별 발전소 선택과 전체 선택 모두 `scope='all'`이 되어 같은 active PK를 갱신했다. `/api/v1/reports?period=2024-04`에는 전체 보고서 하나만 남았다. 원래 개별 보고서 ID의 조회는 HTTP 200이었다.

**영향:** 서로 다른 선택 범위의 최신 보고서를 독립적으로 찾지 못한다. 오래된 보고서 HTML/CSV/manifest 바이트를 덮어쓰거나 ID 기록을 삭제한 문제는 아니다. `all-public`, `all-synthetic` 같은 문자열도 같은 설계 위험이 있고, 발전소를 지정하면 `source_kind`가 active scope에 포함되지 않는 점도 정적으로 확인된다. 후자의 데이터 조합까지 별도 재현한 것은 아니다.

**최소 개선:** 표시용 scope와 active 식별자를 분리하고, `(plant_id 또는 null, source_kind 또는 null)`를 충돌 없는 구조/정규 직렬화로 표현한다. 기존 ID/불변 파일은 보존하며 새 active 키의 호환 이관을 명시한다. 기존 보고서 관련 검사에 `all` 발전소와 전체 범위가 공존하는 사례 하나를 추가하는 정도면 충분하다. 도구나 서비스 추가는 필요 없다.

### L1 — 원본에서 인버터가 사라지면 분모도 감소함: 알려진 제한을 재현

위치: `src/solarops/pipeline.py:242–249,432–436`; `src/solarops/analytics/metrics.py:25–49`; `docs/data-contract.md:41,49`.

두 인버터의 같은 1슬롯을 게시한 뒤 하나만 있는 새 source_version을 게시했다. expected_slots는 **2→1**, coverage는 **1.0→1.0**이었다. 새 `source_inverter_bounds`에서 ID 2가 사라진 것도 확인했다. 날짜 전체가 원본 범위 밖으로 빠지는 경우에만 기존 shrink guard가 작동하므로 문서와 일치한다.

**영향:** 원본 잘림/설비 목록 변화가 데이터 품질 개선처럼 읽힐 여지는 있다. 독립 설비 목록이 없는 상황에서 이전 인버터를 임의 가동 설비로 채우는 것도 정답이 아니다. 현재는 관측 기준이라는 문구와 ID/범위/개수 계보로 감사 가능성을 확보한다.

**최소 개선:** 과거와 새 manifest의 인버터 집합/범위 차이를 안전한 검토 경고로 보여주면 해석 부담을 줄일 수 있다. 실제 가동기간이나 고장을 추론하거나 자동 철회할 필요는 없다. 고정 BR 공개 자료의 계약 한계로 보며, 무조건 게시 거부나 신규 설비 관리 시스템을 요구하지 않는다.

### S1 — 일부 조회는 응답 limit 전에 전체 결과를 물질화함: 정적 관찰

위치: `src/solarops/api/app.py:177–185,196–202,288–320`; `src/solarops/storage/postgres.py:183–197`.

일별 metric/issues 조회와 보고서 목록은 DB 또는 객체 결과를 먼저 모은다. 현재 포트폴리오 데이터 규모의 장애를 직접 재현한 것은 아니며, README의 전체 규모로 불가능한 구조라고 결론내리지 않는다. 장기 이력이나 큰 보고서 목록에서는 응답 limit이 메모리/객체 I/O 한도를 뜻하지 않는다. 최소 대응은 실제 목록 크기/지연을 측정하고 필요한 endpoint만 SQL 페이지 또는 제한을 적용하는 것이다. 기존 실행 이력의 SQL 페이지/인덱스를 다른 조회 전체의 성능 근거로 일반화하면 안 된다.

### S2 — 운영·성능 증거의 독립 재생 범위

`docs/benchmarks/technical-20261023.md:53`은 상세 부하 probe와 원시 지연을 Git 제외 아티팩트에 둔다. 제공된 요약·조건은 유용하지만 이 스냅샷만으로 해당 p95를 원시 표본에서 독립 계산하지 못했다. 전체 원본을 커밋할 필요는 없다. 필요하다면 비밀/원본행 없는 압축 원시 지연, 실행 명령, 사용 probe 해시를 소형 증거 번들로 남기는 것이 최소 개선이다. 제외된 worklog/plan 링크 자체는 이 지적의 근거가 아니다.

## 역사 증거와 미검증 범위

문서에 적힌 51개 발전소·14,400,480행·12,572개 파티션, 실제 ONS 167,424행·51일, 공개 KPO 직렬/병렬 시간, 복원 27객체, 두 OS CI, 화면/접근성 확인은 **원 작성자의 버전별 역사 증거**다. 이번 평가가 그 전체를 독립 실행한 것으로 계산하지 않았다. 새 실제 서비스 검사는 합성 자료의 현재 게시·동시성 계약을 뒷받침하지만 운영 중 Compose/kind의 배포 상태까지 인증하지 않는다.

신규 머신 의존성 설치·wheel 설치·이미지 빌드·Airflow/Kubernetes·브라우저/보조공학·현재 외부 ONS HTTP·전체 공개 데이터·백업 복원·장시간 부하는 실행하지 않았다. 고객 인증·영업·현장 고장 정답·금전 손실·다중 물리 호스트 가용성은 범위 밖이다. 이 부재만을 이유로 특정 기술이나 상용 기능을 추가하라고 제안하지 않는다.

원문 출처/모델 요청/명령/실제 경로 및 서비스 이미지 식별자는 [astra-provenance.md](astra-provenance.md)에 별도 보존했다. 이 평가의 5점은 해당 로컬 범위의 재현 가능한 근거를 뜻하며 무결점·외부 감사·품질 인증을 뜻하지 않는다.
