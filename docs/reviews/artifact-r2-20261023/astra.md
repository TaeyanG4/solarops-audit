# SolarOps Audit 독립 산출물 평가 — Astra R2

2026-10-23 Asia/Seoul. **총점 97/100**. 고정 `portfolio-rubric.md` v1의 20개 항목을 각각 0~5점으로 평가했다. 평가 대상은 `dbfb04ca4a3a9bf7c0f9e2b7de552079b2312cf5`, 구현 `038a000b69befaa77efd918a0b9654ba866ce501`, 앱 v0.5.3 / 계산 energy-interval-v2다. 면접·개인 역량·채용 판단은 포함하지 않는다.

공개/합성 자료의 로컬 배치 포트폴리오로서, 계약이 실제 파서·계산·게시 코드에 연결되고 실패·충돌·정정의 의미를 검사로 입증한다. 이번에 직접 실행한 핵심 검사 **79개 모두 통과(26.91초)**, 별도 합성 7일 데모의 실패 보존·재처리 해시 일치·보고서 생성, 릴리스 선언 정렬을 확인했다. 이 검토 범위에서 데이터 오게시·조직 간 노출·복구 실패를 재현하지 못했다. 감점 3점은 진단 위치 정보, Airflow 설치 산출물의 재현 강도, 현재 상태 문서의 버전 연결에 한정한다.

5점은 이 범위에서 코드·검사·재현 절차가 충분하고 확인된 미해결 문제가 없다는 판단이다. 전체 입력 공간의 무결점 보증이나 모든 과거 인프라 실행의 재수행을 뜻하지 않는다. 평가 원문을 읽은 범위와 실제 실행은 별도 `astra-provenance.md`에 기록했다.

| 번호 | 영역 / 고정 세부 항목 | 점수 | 실제 근거와 판단 |
|---:|---|---:|---|
| 1 | 데이터 / 출처·단위·시간 계약 | 5 | `docs/data-contract.md`, `docs/ons-source-contract.md`; `normalize/parquet.py:67`, `acquisition/ons.py:38`. BR의 UTC·15분·추정 kWh와 ONS의 MWmed·미상 시간대·예측 구분이 코드와 일치. 타임스탬프·오프셋 검사를 직접 실행했다. |
| 2 | 데이터 / 파싱·정규화·충돌 | 5 | `contracts/brpvgen.py:60`, `normalize/parquet.py:92`, `pipeline.py:85`; metadata 모호성, canonical int64 ID, 동일/충돌 중복, 원본 변경 후 보존 사본 처리 검사가 통과했다. 원문 CSV와 추가 필드 계보를 남긴다. |
| 3 | 데이터 / 품질 분모·unknown·0 | 5 | `analytics/metrics.py:13`, `reports/render.py:43`, `api/static/dashboard.js:71`. 관측/유효/누락을 구분하고 DST 92/100슬롯, 무효만 있는 시계열 null, 실제 0, 전부 불명/혼합/False 보고서 검사를 직접 실행했다. 기존 v2 비중과 unknown 수를 함께 해석하는 계약이 명시돼 있다. |
| 4 | 데이터 / 증분·정정·철회 | 5 | `acquisition/ons.py:246`, `:297`, `:343`, `pipeline.py:242`; ONS 변경일·철회·304·실패 cursor·경쟁, BR 범위 축소 거부·선택일 재처리가 검사로 확인된다. BR의 제한된 upsert와 ONS 월 snapshot을 혼동하지 않는다. |
| 5 | 데이터 / 계보·결과 동등성 | 5 | `pipeline.py:127`, `:387`, `:421`, `reports/render.py:25`; raw SHA, 자연키 정렬 논리 해시, 실행·보고서 계보가 연결된다. 직접 7일 반복 해시와 과거 보고서 불변을 확인. 역사 근거 `integrity-v0.4.2.md`, `stack-authenticity-20261023.md`는 환경 간/원본 독립 계산의 구체적 수치를 제공한다. |
| 6 | 신뢰성 / 원자 게시·실패 보존 | 5 | `storage/minio.py:42`, `pipeline.py:448`, `reports/render.py:115`, `acquisition/ons.py:297`. 완성 raw의 원자 링크, 객체 선저장·DB 포인터 전환, 보고서 upload/DB 실패 및 during-commit rollback 검사를 직접 확인. 일별/월별 경계와 미게시 객체 보존이 정확히 설명된다. |
| 7 | 신뢰성 / 동시성·재시도 | 5 | `pipeline.py:176`, `:451`, `storage/postgres.py:108`; 같은 버전 상이 입력과 겹치는 날짜의 느린 배치를 차단하는 실제 스레드 검사가 통과. 보고서 역순 완료·명시적 restore도 검사했다. 실제 PostgreSQL 및 KPO 재시도는 역사 근거로만 채택한다. |
| 8 | 신뢰성 / 조직·경로·비밀 경계 | 5 | `storage/postgres.py:161`, `api/app.py:68`, `replay.py:18`, `contracts/brpvgen.py:39`; 조직별 조회·객체 네임스페이스, ZIP 경로 검사, 읽기 API 초기화 금지, 오류 sentinel 비노출을 직접 확인. 관리 앱은 `admin/app.py:29`의 loopback/Host/Origin/token 경계를 코드 검토했다. 고객 인증 부재는 감점하지 않았다. |
| 9 | 신뢰성 / 진단·복구 절차 | 4 | `diagnostics.py:12`, `docs/runbooks/recovery.md`, `docs/runbooks/backup-restore.md`는 active·자식·재시도와 프로세스 생존을 구별한다. 다만 비수치 입력의 안전한 실패 기록에서 파일 종류·행/컬럼 위치가 사라지는 제한을 직접 재현했다(F1). |
| 10 | 신뢰성 / 회귀 검사의 의미·실제 실행 | 5 | 기존 5개 관련 파일의 79개 검사를 한 차례 실행했다. 단순 성공 스냅샷보다 실패 시 기존 게시 결과·원본·metadata·조직 경계·실제 동시 실행을 검사한다. `.github/workflows/ci.yaml`의 양 OS 경로와 선택형 서비스 CI를 구분한다. 전체 회귀나 서비스 검사를 이번에 실행했다고 주장하지 않는다. |
| 11 | 아키텍처 / 역할·공통 CLI | 5 | `cli.py`, `dags/solarops_factory.py:25`, `pipeline.py`, `reports/render.py`, `api/app.py`; DAG가 계산을 복제하지 않고 같은 CLI를 호출한다. 읽기 앱과 호스트 관리 앱, 앱 DB와 Airflow 메타 DB가 분리돼 있다. |
| 12 | 아키텍처 / 저장·조회 모델과 제약 | 5 | `storage/postgres.py:36`, `:161`, `api/readmodels.py:51`, `:158`; active 복합키·버전 claim·한 SELECT snapshot·슬롯 가중 집계·조직 표현식 인덱스가 용도와 맞는다. FK 없는 JSON 중심 모델의 무결성을 쓰기 경로와 회귀로 지키며, 이 규모에서 별도 모델 도입을 요구할 근거는 없었다. |
| 13 | 아키텍처 / 기술 선택·비용·대안 | 5 | `docs/architecture/technology-stack.md`는 DuckDB의 512MB가 프로세스 전체 한도는 아님, Pod 기동·소규모 Parquet·JSON 조회·Airflow 비용을 명시한다. 도구 수보다 처리 규모와 측정된 병목에 선택을 연결한다. Kafka/Spark 미사용은 감점 사유가 아니다. |
| 14 | 아키텍처 / 배포 버전·설정과 운영 경계 | 5 | `src/solarops/release.json`, `docs/releases/0.5.3.json`, `runtime.py`, `dags/solarops_factory.py`; 구현 SHA·이미지 ID·계산 버전·실행/Pod identity를 분리한다. `release.py check`를 직접 통과했고 `quality-v0.5.3.json`은 배포와 신규 scheduled KPO 미실행을 구분한다. |
| 15 | 재현성 / 새 환경의 작은 오프라인 시연 | 5 | README의 네 명령과 `scripts/demo/portfolio_demo.py`는 Docker/원본 없이 독립 SQLite 시연을 만든다. 이번 실행에서도 새 경로, 7일 active, 실패 1회/성공 2회, 해시 일치, 부분 기간 보고서를 확인했다. 최초 설치 네트워크와 새 환경 CI의 역할이 문서화돼 있다. 이번에는 기존 venv를 사용했다. |
| 16 | 재현성 / 의존성·실행 버전·이미지 추적 | 4 | 앱은 Python 3.12·uv.lock 해시, 기반 이미지 digest, release/image ID로 추적된다. MinIO 소스 checksum 고정도 확인했다. Airflow 추가 설치는 버전 constraints로 제한되지만 배포 파일별 해시 강제는 아니다(`Dockerfile:22`): A1의 재현 제한으로 1점 감점. |
| 17 | 재현성 / 측정 절차·원본 요약·재현 한계 | 5 | `quality-v0.5.3.md/json`, 허용된 `2026-10-23-bounds-reproduction.md`, `incremental-v0.5.0.md/json`에 원본 크기·hash·순서·시행별 시간·동등성·범위가 있다. 0.674→3.527초의 범위 계산 비용도 숨기지 않는다. 단일 호스트 1회 DAG 비교를 일반 확장성으로 확대하지 않는다. |
| 18 | 전달력 / 처음 보는 사람의 README 동선 | 5 | 문제·5분 합성 시연·원천·숫자 의미·설계·증거·한계 순으로 구성돼 있다. 설치와 운영을 선택 경로로 분리하고 구체적인 다운로드/추정치/부분 기간을 설명한다. 현재 PC를 요구하지 않는 경로가 첫 화면에 있다. |
| 19 | 전달력 / 주장과 코드·근거 연결 | 5 | README→계약/ADR/벤치마크→코드/기계 판독 JSON으로 연결된다. 51개 전체, 4월 5개, kind 공개 하루, 실제 ONS 51일의 범위를 구별한다. 논리 hash와 HTTP/파일 SHA도 혼동하지 않는다. |
| 20 | 전달력 / 현재·과거 증거·미완료 구분 | 4 | README와 최신 benchmark는 과거 검사·최신 배포·미실행을 대체로 잘 구분한다. 그러나 `IMPLEMENTATION_STATUS.md:3`은 v0.5.3을 현재로 두면서 `:5`의 '최신 경계 보완'은 v0.5.2를 안내한다(F2). 이 평가에서 금지된 handoff/plan의 정확성은 판단하지 않았다. |

영역 합계: 데이터 **25/25**, 신뢰성 **24/25**, 아키텍처 **20/20**, 재현성 **14/15**, 전달력 **14/15**.

## 확인 사항과 최소 개선

**F1 — 낮음(P3), 실패 원인 위치의 관찰 공백. 재현됨.** `src/solarops/normalize/parquet.py:96`의 비수치 전력 변환 오류는 `src/solarops/contracts/brpvgen.py:49`에서 `BR_INPUT_INVALID`로 안전하게 분류된다. `src/solarops/pipeline.py:260`에서 일별 실행 생성 전에 발생하면 `:311`이 batch 실패만 남긴다. 새 합성 입력의 세 번째 자료 행에 `synthetic-nonnumeric`을 넣은 한 번의 실행에서 `failed / processing_partitions / BR_INPUT_INVALID` 하나, active 0개, quarantine 0개를 확인했다. 오류 코드에 입력 종류·컬럼·원본 행 위치가 없어 대용량 원본에서 진단이 불편하다. 안전하게 거부했다는 점은 정상이며 데이터 무결성 결함으로 분류하지 않는다. 최소 개선은 원문 값·접속 정보 없이 허용된 `dataset_kind`, `field`, 가능한 원본 레코드 번호를 안전한 오류 문맥에 추가하는 것이다. 기존 실패 검사에 이 문맥과 비노출을 함께 검증하면 충분하고 별도 검사 도구는 필요 없다.

**F2 — 낮음(P3), 현재 상태 문서의 최신 링크 불일치. 정적 확인.** `docs/IMPLEMENTATION_STATUS.md:3,5,53`의 현재 버전/최신 설명은 v0.5.3과 v0.5.2가 섞여 있다. README의 최신 v0.5.3 링크는 올바르므로 첫 실행을 막지는 않는다. 최소 개선은 현재 요약을 v0.5.3 근거에 연결하고 v0.5.2 문장을 명시적 과거 설명으로 옮기는 것이다. 과거 benchmark 원문은 보존하고 문서 링크 확인만 수행하면 된다.

**A1 — 낮음, 의존성 재현 제한. 실행 결함으로 단정하지 않음.** `infra/docker/Dockerfile:22`는 Airflow 설치에 constraints와 `pip check`를 쓰며, `infra/docker/airflow-constraints-3.12.txt`는 버전 목록이다. 앱의 uv.lock처럼 다운로드 파일별 hash를 강제하지 않는다. 기반 digest·constraints 자체 SHA·결과 이미지 ID가 있어 대표 실행의 추적은 충분하나, 같은 설치 산출물을 다시 얻는 보장 강도에는 차이가 있다. 최소 보완은 다음 정식 이미지 갱신 때 실제 추가 설치 파일들의 해시를 고정하거나, 재사용할 검증 이미지 자체의 불변 배포·보존 경로를 명확히 하는 것이다. 현재 릴리스의 캐시 없는 재빌드 실패나 공급망 사고는 관찰하지 않았으며 이를 주장하지 않는다. 새 기술 도입이나 반복 빌드를 이번 평가의 완료 조건으로 요구하지 않는다.

P0/P1/P2 수준의 확인된 결함은 이번 검토에서 없다. 보고서의 시각 기반 active 선택, 미게시 객체의 수동 보존, ONS 최근 20회 조회, BR 철회 미지원은 문서화된 범위와 설계 선택으로 읽었으며 별도 결함 점수를 부과하지 않았다.

## 실행 근거와 한계

- 직접 실행: Python **3.12.13**, uv **0.11.29** 확인; 계약·파이프라인·계산 v2·게시 경계·무결성 경계 **79 passed / 26.91s**; 새 경로의 합성 7일 데모; `release.py check` 성공; F1의 합성 비수치 입력 한 번.
- 데모: `artifacts/astra-r2-synthetic-20261023/evidence.json`, active 7, `failed_publish_kept_active_data=true`, `replay_hashes_identical=true`, batch committed 2 / failed 1. 첫날 논리 hash `203fa93c53bb9bb92260715c813575824a9f1264d614b76fc8c02045bba16ebd`. 보고서 ID `92df7d28-e88c-49a7-939b-7592ccce72b6`, `partial_period`.
- 역사 근거로만 검토: quality-v0.5.3 JSON의 offline `tests=154, skipped=14, failures=0, errors=0`, services `tests=13, skipped=0`; 구현 CI success·배포 health/ready·양 모드 7 DAG. JSON의 `tests`를 이번 직접 통과 수나 무조건 154 passed로 바꾸지 않았다. v0.4.2의 환경 간 합성 동등성, v0.5.0의 실제 ONS/KPO, v0.4.0 복원·계산 전환, 공개 원본 독립 계산 기록도 과거 증거다.
- 미실행: 새 clone/의존성 설치, 전체 회귀·lint·wheel 빌드, 실제 PostgreSQL/MinIO 서비스 검사, Docker/Helm/Kubernetes 변경, 신규 scheduled KPO, HTTP 원천 다운로드, 공개 전체 재처리, 브라우저 조작·접근성 검사, 별도 호스트 복원. 서비스 상태·원격 CI 성공을 이번에 독립 조회한 것도 아니다.
- 범위 밖: 고객 인증·공개 서비스 운영·상업 성과·확정 고장/손실·다중 호스트 HA·Kafka/Spark 보유 여부. 부재를 감점하지 않았다. 에너지는 추정, 성능 표시는 검토 후보로 유지한다.

원본·기존 DB·서비스·과거 보고서를 수정하지 않았고, 새 영구 테스트나 검증 스크립트도 추가하지 않았다. 점수는 산출물의 확인 범위에 대한 판단이며 외부 품질 보증을 대체하지 않는다.
