# SolarOps Audit — Codex 단계별 구현 지시서

> 이 문서를 Codex에 전달할 때 `01_MASTER_PRD.md`를 함께 읽도록 한다. 이 지시서는 **실제 구현 방법, 파일, 완료 기준, 테스트**에 우선순위를 둔다. 전체 프로젝트를 한 번의 프롬프트로 구현하지 말 것.

## A. 모든 Codex 작업에 적용하는 협업 계약

1. 저장소가 비어 있으면 `solarops-audit` 루트에서 시작. 이미 파일이 있으면 `git status`, 파일 구조 확인 후 변경 범위를 요약한다. 관련 없는 기존 코드는 수정하지 않는다.
2. 각 작업은 `목표 → 변경 파일 → 설계 결정 → 실행한 명령 → 테스트 결과 → 미완료·위험`을 짧게 보고한다.
3. 테스트를 수행하지 못하면 **실행하지 못했다고 명시**하며 통과한 것처럼 기술하지 않는다. PC 접근/네트워크/권한 불가 시 모의하지 않고 차단 사유와 정확한 수동 검증 명령을 제공한다.
4. Python은 3.12 기준. 버전은 `uv.lock` / 이미지 digest 또는 명시 태그 / Helm Chart 버전에 고정. `latest` 금지.
5. 보안: `.env`/API 키/고객 CSV/원본 아카이브를 commit하지 않는다. `.env.example` 및 합성 fixture만 버전 관리.
6. 구현 우선순위는 **CLI → 데이터 계약/검증 → 스토리지 → Airflow → Kubernetes → 리포트**. DAG 내부에 업무 로직을 중복 작성하지 않는다.
7. 수집된 BR-PVGen은 전처리·보간된 역사 데이터. 라이브 데이터를 가장하거나 실제 고장을 확정하지 않는다.
8. 처음부터 모든 자료를 다운받지 말 것. `make test`는 인터넷이 없어도 빠르게 실행되고, 전체 351MB 다운로드는 명시적 `make download-full`에서만 발생한다.
9. 모든 SQL/스토리지 기록은 재실행/장애 상황에서 중복이 발생하지 않도록 설계한다. 결과 공개는 staging 검증 후 원자적으로 변경한다.
10. 모든 CLI·Makefile·Docker 커맨드는 WSL2 Ubuntu에서 재현 가능하도록 작성한다. `/mnt/c`보다 `~/projects` 권장.
11. 고객의 실제 발전소 데이터를 GitHub 등에 공유하지 않는다. 개발 중 보고서는 로컬 또는 접근제어된 영역만 사용.
12. 한 단계가 끝나면 다음 단계로 넘어가지 말고 완료·한계·선택 필요 사항을 보고한다.

## B. 구현 전에 기록할 ADR (Architecture Decision Record)

- `docs/adr/0001-data-processing.md`: Polars/Arrow/duckdb 파일 포맷/메모리 모델 결정.
- `docs/adr/0002-two-environments.md`: Compose와 kind가 독립적인 스토리지를 갖는 이유.
- `docs/adr/0003-kpo-not-executor.md`: Airflow LocalExecutor + KubernetesPodOperator 선택 근거 및 Provider 버전.
- `docs/adr/0004-data-quality.md`: 전처리된 공개 자료의 보간과 결측 해석 제한.
- `docs/adr/0005-business-scope.md`: 고객 파일 업로드/결제/멀티테넌트 제외 이유.

## C. 단계별 작업 백로그(각 단계는 별도 Codex 요청)

### M0 — 저장소 및 개발 환경
**요구사항:** `README.md`, `AGENTS.md`, `.gitignore`, `.env.example`, `pyproject.toml`, `uv.lock`, `Makefile`, `src/solarops/__init__.py`, CI 초안, `docs/adr` 골격.

**명령 목표:**
```bash
make doctor            # python, uv, docker, compose, 디스크/메모리 확인; 부재 시 명료한 메시지
make lint              # Ruff
make test              # 오프라인 fixtures만으로 pytest
```
**인수 조건:** 빈 저장소에서 의존성 설치 및 테스트 가능; 원본 데이터 다운로드 없음; `git status`에 비밀값/대용량 원본 없음.

### M1 — 실제 소스 계약 검증과 다운로드 도구
**구현:** `acquisition/brpvgen.py`, `contracts/brpvgen.py`, `cli.py`의 `source inspect`, `source fetch --files ...`, `source checksum` 서브커맨드.

**반드시 검증할 사실:**
- 공개 metadata CSV의 `id`는 `PS_001` 같은 **문자열**(README 설명 중 integer 서술과 불일치).
- inverter zip 안 파일당 `datetime`, `inverter_id`, `ps_id`, `total_active_power_w`, `interpolated_keys_*` 등의 실존 여부는 **실제 파일을 읽어 확인 후 매핑**한다.
- `datetime` UTC `Z`; 발전소별 시작/종료 기간 다름.
- 게시된 MD5 검증 및 실제 SHA-256 계산.
- ZIP 파일의 경로 안전성, 확장 파일 크기 상한, 다운로드 파일의 스키마 불일치 대응.

**인수 조건:** synthetic CSV로 오프라인 통과; 실제 metadata.csv만 다운로드하는 옵션에서 `PS_001` 인식; 대용량 파일 비자동 다운로드.

### M2 — 저장소·정규화·품질검사
**구현:** `storage/minio.py`, `storage/postgres.py`, `normalize/parquet.py`, `contracts/quality_rules.py`, `migrations/`, CLI `ingest --plant PS_001 --from --to --source-version v1`.

**정규화:** 발전소/인버터/시간대별 15분 관측값을 Parquet에 스트리밍/청크 기록. 업로드 파일·버전·행수·단위·보간 플래그를 모두 보존.

**결과 반영:** raw는 버전 불변, curated는 검증 성공 후 커밋, 실패는 격리(쿼런틴)·실패 코드 기록. DB에는 실행/품질/일별 집계 메타정보 중심으로 저장.

**인수 조건:** 같은 샘플 3회 ingests 후 데이터 행수/정규화 결과 해시 동일, 실패한 실행은 이전 정상 마트를 덮지 않음, `source_object` 계보 추적 가능.

### M3 — 집계·검토 대상·리포트
**구현:** `analytics/metrics.py`, `analytics/rules.py`, `reports/render.py`, `templates/monthly_report.html`, CLI `analyze`, `report`.

**필수 규칙:**
- `estimated_energy_kwh = sum(active_power_w / 1000 × 0.25)` (명시적 근사, 불완전 시계열 통제).
- 소스 보간율, 기대 슬롯 대비 관측 비율, 미관측/미유효 구간 구분.
- 야간 0출력은 경고 아님. `POA>=400` 및 `power/capacity<0.10` 3회 연속 조건(설정 가능한 초기 가설)으로 **검토 필요**만 표시.
- 실제 고장 정확도·실제 손실액 출력 금지.

**Golden fixture 예시:** 합성 발전소 `DEMO_01`에서 인버터 2대의 15분 전력값이 처음 두 슬롯에 각각 (1kW+2kW), (2kW+3kW)이며 뒤 구간은 누락된 경우, 단순 추정 발전량은 `(3+5)×0.25 = 2.0kWh`다. 누락 구간을 0 출력으로 간주하거나 앞 값으로 채우지 않는다. 같은 입력 파일에 중복 행을 추가해도 결과는 2.0kWh여야 한다. 3번째 슬롯이 소스 보간 값이라면 존재하더라도 보간 비율에 따로 기록한다.

**인수 조건:** 리포트에 기간·UTC/표시 타임존·소스 라이선스·데이터 버전·규칙 버전·결측/보간 구별 표시. synthetic fault fixture 결과 결정적.

### M4 — Docker Compose 반복 실행 가능한 로컬 환경
**구현:** `infra/docker/`, `infra/compose/compose.yaml`, `scripts/bootstrap-local.sh`, Make target `up-local`, `down-local`, `demo-sample`, `db-migrate`.

**서비스:** 애플리케이션 PostgreSQL, MinIO, 작업 CLI 이미지, 필요 시 로컬 Airflow 개발 스택. Airflow Metadata DB는 별도이며 앱 DB와 데이터 혼합 금지.

**인수 조건:** `make up-local` / `make demo-sample`가 최초 실행 시 데이터 샘플 생성 → 정규화 → QA → 리포트를 생산, 서비스에 고정 비밀번호 하드코딩 없음.

### M5 — Airflow DAG 3종 + Backfill
**구현:** `dags/solarops_ingest_daily.py`, `dags/solarops_quality_daily.py`, `dags/solarops_report_monthly.py`, `dags/solarops_backfill_manual.py` 및 `docs/runbooks/dags.md`.

**요구사항:**
- 정확한 DAG ID와 흐름은 Master PRD 8장 참조.
- 데이터 집합의 과거 재생 모드와 신규 고객 파일 도착 모드 구별.
- `catchup=False` 기본, 명시 Backfill 작업만 과거 처리; timeouts, retries, backoff, max_active_runs 정의.
- UI 파라미터 범위 제약·dry_run 지원.
- Airflow TaskFlow/KPO 호출은 외부 CLI 함수에 필요한 ID만 전달(XCom 큰 배열 금지).

**인수 조건:** DAG import 오류 0, 정상 실행 1회 + 재시도 1회 + Backfill 1회 스크린샷/로그.

### M6 — kind + Helm + Kubernetes 작업
**구현:** `infra/kind/cluster.yaml`, `infra/helm/airflow-values.yaml`, `infra/k8s/`(DB, MinIO, Secret placeholder, serviceaccount, RBAC), `scripts/k8s-*`, `Makefile`.

**핵심 설계:**
- 공식 Airflow Helm Chart 사용, Chart/앱 버전 테스트 후 핀 고정. `executor: LocalExecutor` + `KubernetesPodOperator`로 별도 작업 Pod 생성.
- Task Pod는 서비스 어카운트·CPU/RAM requests/limits·Job timeout·pod delete 정책 설정.
- 작업 이미지 로컬 빌드 및 `kind load docker-image solarops-worker:<immutable-tag>` 사용. Pod imagePullPolicy 명시.
- 환경별 DB·MinIO를 분리하여 local K8s 내 서비스 DNS 경유. Compose 컨테이너 네트워크에 대한 암묵적 의존 금지.

**인수 조건:**
```bash
make k8s-bootstrap
make k8s-deploy
make k8s-smoke
kubectl get pods -n solarops
```
하나의 DAG 태스크가 실제 작업 Pod로 생성되고 상태/로그/결과가 확인된다. Helm rollback 절차를 문서화한다.

### M7 — 장애 주입·성능·관측성
**구현:** `tests/integration/test_idempotency.py`, `tests/k8s/`, `scripts/fault-injection.sh`, `docs/runbooks/recovery.md`, `docs/benchmarks/`.

**실험:**
1. 동일 입력 3회 재처리 → 행수·결과 checksum 동일.
2. 중간 쓰기/스키마 오류 → publish 마트 교체 없음, 오류 추적 가능.
3. 실행 Pod 강제 종료 → Airflow 실패/재시도 확인, 재실행 후 정상 완료.
4. 날짜별 백필 → 지정되지 않은 파티션/보고 결과 변화 없음.
5. 1·2·4 Pod → 동일 데이터의 총 시간·CPU·최대 RAM·오류 수 비교. 속도 개선을 허위로 주장하지 않음.

**인수 조건:** `docs/benchmarks/YYYY-MM-DD.md`에 CPU/메모리/OS/WSL/Docker/Airflow/K8s/데이터 크기/측정 명령/원본 결과 기록.

### M8 — 파일럿용 UI/API 및 종합 문서
**구현:** `src/solarops/api`(read-only), 선택 Streamlit, 보고서 UI, `docs/runbooks/operator.md`, 최종 `README.md`, 데이터 라이선스 인용.

**인수 조건:** 사업 담당자가 월간 보고·이슈 조회를 5분 이내 시연할 수 있음. 인터넷 공개 금지 상태를 기본으로 명시. 사용법·제한사항·운영 책임을 알 수 있음.

### M9 — 사업 파일럿 준비(사람의 확인 필수)
**구현 대상 아님:** 고객 인터뷰 10곳, 연락·개인정보 동의, 실제 데이터 수령 계약, 유료 제안, 보고서 해석 검수, 결제.

**Codex 산출물:** CSV 스키마 매핑 템플릿, 파일럿 설명서 초안, 고객별 보고서 샘플, 비식별 수집 체크리스트, 가격 시뮬레이터(가설값과 비용 구분).

**인수 조건:** 고객 파일이 외부 업로드/공개 저장소에 자동 전송되는 기능 없음; 고객 승인 전 파일럿 적재 금지.

## D. Codex에 실제로 입력할 최초 프롬프트

```text
프로젝트: SolarOps Audit.
먼저 저장소의 `01_MASTER_PRD.md`, `02_CODEX_EXECUTION.md`(또는 내가 첨부한 동명 문서)를 읽어라.
이번 작업 범위는 M0만이다. M1~M9는 구현하지 마라.
개발 환경은 Windows + WSL2 Ubuntu + Docker Desktop이며, Python 3.12를 사용한다.
지시서의 공통 계약과 비범위를 반드시 지켜라.
1) 기존 파일과 git 상태를 확인하고 10줄 이내로 작업 계획을 제시해라.
2) M0의 파일만 생성/수정해라. 내 데이터 파일이나 다른 프로젝트는 건드리지 마라.
3) 오프라인으로 실행되는 pytest 샘플 1개와 Ruff 검사를 추가해라.
4) make doctor, make lint, make test의 성공/실패를 실제로 실행하고 보고해라.
5) 변경 파일, 실행 명령, 통과한 테스트, 미해결 이슈를 정리한 뒤 멈춰라.
명확하지 않은 사양은 최소·안전 기본값을 택하고 ADR/README에 적어라.
```

## E. 다음 단계 요청 템플릿

```text
SolarOps Audit의 M{번호}만 구현해라.
먼저 01_MASTER_PRD.md와 02_CODEX_EXECUTION.md의 관련 섹션을 읽고 이전 구현의 테스트 상태를 확인해라.
이번 단계 범위를 벗어나는 기능은 만들지 마라.
공통 구현 계약(비밀값 금지, 데이터 라이선스, 합성/실제 구분, 재현성, 정확한 로그)을 따르라.
1. 구현 전 변경 파일 목록 및 검증 계획 제시.
2. 요구사항에 맞춰 구현, 자동 테스트 추가.
3. 실제 실행한 명령/결과를 보고. 수행 못한 테스트는 미수행으로 명확히 기재.
4. 인수 조건 충족 여부와 남은 위험 정리 후 중단.
```

## F. GitHub PR 표준

```text
## 왜 필요한가
[고객 또는 운영 문제가 무엇인지]
## 변경 범위
[코드/인프라/문서]
## 검증
[명령, 원본 결과, 재현성]
## 자료/보안
[합성/공개/고객 데이터 구분, 라이선스]
## 위험 및 롤백
[실패 시 되돌리는 방법]
## 다음 단계 차단 조건
[현재 미완료 사항]
```

## G. 운영 커맨드 인터페이스(최종 구현 목표)

```bash
make doctor            # 도구, 디스크/메모리/연결 체크
make lint
make test              # offline unit + contract fixtures
make download-metadata # 매우 작은 파일만 실제 다운로드
make download-full     # 전체 공개자료 명시적 다운로드만
make up-local
make db-migrate
make demo-sample       # 합성 또는 공개 소량 샘플, 전체 다운로드 불필요
make dag-validate
make k8s-bootstrap
make k8s-deploy
make k8s-smoke
make down-local
```

명령이 제공되기 전에 사용자에게 해당 명령이 이미 동작한다고 표현하지 않는다. M0부터 각 단계에서 순차적으로 구현한다.

## H. 구현 종료 시 3분 시연 시나리오

1. 공개 데이터 출처, 파일 버전, 보간 여부를 화면에서 확인한다.
2. `make demo-sample`과 Airflow DAG 실행, 정상 보고서 생성 결과를 보여준다.
3. 일부 데이터 누락을 합성 주입하고 **소스 보간과 새 결측**을 다르게 표시한다.
4. 같은 날짜를 3회 재처리해 일별 지표 checksum이 동일함을 보여준다.
5. Airflow가 Kubernetes 작업 Pod를 생성하는 모습과 Pod 강제 종료 후 복구를 보여준다.
6. 유료 제품 후보인 월간 운영보고서(출처·신뢰도·검토 대상)를 보여준다.
7. 실제 고객 파일이 아직 없다면 '공개 데이터 데모'임을 명시한다.

## I. 스프린트 종료마다 사용자에게 보고할 표

| 항목 | 보고 내용 |
|---|---|
| 완료된 범위 | M번호 / 기능 / 파일 |
| 실제 테스트 | 명령 / 성공 또는 실패 로그 |
| 미실행 테스트 | 이유 / 필요한 환경 |
| 데이터 | 합성/공개/고객 여부 |
| 성능 | 입력 크기 / 시간 / 최대 RAM |
| 장애/제약 | 재현 단계와 우회책 |
| 다음 단계 | 실행 준비 여부 |

