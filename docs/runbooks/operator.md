# 운영자가 확인할 순서

## 시스템 관리 8504

[분석 화면 8502](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public)과 [관리 화면 8504](http://127.0.0.1:8504/)는 별도 프로세스입니다. 관리 서버는 대시보드 컨테이너를 멈춘 뒤에도 다시 켤 수 있도록 **호스트 Python**으로 실행됩니다. Docker Desktop은 먼저 켜져 있어야 합니다.

분석 사이드바의 **시스템 관리**를 누르면 중간 열기 버튼 없이 바로 이동합니다. **서비스 제어**에서 시작·중지, **컨테이너 상태**에서 실행/건강/준비 상태, **운영 안내**에서 범위와 종료 방법을 확인합니다. 방향키·Home/End로 탭을 이동할 수 있으며 `#services`, `#containers`, `#guide` 주소로 바로 열 수도 있습니다. 관리 서버가 꺼져 있다면 아래 실행기로 먼저 켜세요.

저장소 루트의 Windows PowerShell에서:

```powershell
.\scripts\ops\admin.ps1 start
.\scripts\ops\admin.ps1 status
.\scripts\ops\admin.ps1 stop
```

`start`는 숨김 백그라운드 프로세스를 시작하고, `status`는 PID와8504포트의 수신 상태를 확인합니다. `stop`은 이 실행기가 소유한 관리 서버와 venv 자식 프로세스만 종료합니다. 실행 중인 서비스 조작이 끝난 후 사용하세요. PID·stdout/stderr·조작 이력은 Git 제외 `artifacts/ops/`에 남습니다.

다른 OS 또는 보이는 터미널에서 실행하려면 `uv run solarops admin --project-root .`를 사용하고 해당 터미널에서 Ctrl+C로 관리 서버를 종료합니다. 이 Ctrl+C는 Docker 컨테이너를 멈추지 않습니다. 이전 8501/8503 데모 서버를 직접 실행한 경우에만 해당 터미널도 별도로 종료합니다.

| 관리 화면의 대상 | 시작 | 중지 |
|---|---|---|
| SolarOps 작업 환경 | Compose app-db → minio → dashboard | SolarOps kind와 모든 해당 Compose 소비자 → MinIO/DB |
| 대시보드 | 필요한 app-db·minio와 dashboard | dashboard만 |
| PostgreSQL (Compose) | app-db | Compose 소비자(웹·Airflow·worker)를 먼저 멈춘 후 app-db |
| MinIO (Compose) | minio | Compose 소비자를 먼저 멈춘 후 minio |
| Airflow (Compose) | 앱 DB·MinIO·Airflow DB/API/스케줄러/DAG 처리기 | Compose Airflow 구성요소 |
| Kubernetes (kind) | `solarops` kind 노드 | 해당 kind 노드 |

**완전히 끄기:** 관리 UI의 `SolarOps 작업 환경 → 중지`가 완료되면 `admin.ps1 stop`을 실행합니다. **다시 켜기:** `admin.ps1 start` 후 UI의 `SolarOps 작업 환경 → 시작`을 누릅니다. 이 기본 시작은 보고서 조회에 필요한 3개만 켭니다. Airflow와 Kubernetes는 필요할 때 각각 시작합니다.

Compose와 kind 안에는 **서로 다른 DB·MinIO·Airflow**가 있습니다. Compose DB 중지는 kind 내부 DB를 멈추지 않습니다. Docker Desktop에서 보이는 Compose 그룹과 kind 컨테이너의 수는 내부 서비스 수와 다릅니다. 실제 컨테이너 표는 실행·건강 검사·HTTP 준비 상태를 구분하며 kind 실행 중만으로 API/모든 Pod 준비 완료를 보증하지 않습니다.

제어는 이 체크아웃의 라벨·Compose 경로를 확인한 **이미 생성된 로컬 SolarOps 컨테이너**에 한정됩니다. 없는 컨테이너는 [최초 설치](../guides/setup.md)가 필요합니다. 관리 서버는 Docker 엔진 자체, 다른 프로젝트, 컨테이너 삭제·볼륨 삭제·prune·임의 SQL/명령을 제공하지 않습니다. `127.0.0.1:8504` Host/Origin과 CSRF 토큰을 검사하므로 이 주소 그대로 접속합니다. 사용자 인증/원격 관리 기능은 아닙니다.

## 8502가 열리지 않을 때

Docker Desktop 엔진이 실행 중이어도 SolarOps 컨테이너는 중지 상태일 수 있습니다. 저장소 루트에서 상태를 확인하고, 기존 컨테이너를 시작합니다.

```text
docker compose --env-file .env -f infra/compose/compose.yaml ps -a
docker compose --env-file .env -f infra/compose/compose.yaml start app-db minio dashboard
```

대시보드 조회에 필요한 서비스는 **app-db(카탈로그), minio(보고서·파일), dashboard(웹/API)** 세 개입니다. 시작 후 [준비 상태](http://127.0.0.1:8502/ready)가 `ready`인지 확인한 다음 [PS_001 공개 보고서](http://127.0.0.1:8502/?view=reports&period=2024-04&source=public&plant=PS_001)를 새로고침합니다. 대시보드만 켜면 DB나 파일 저장소에 접근하지 못할 수 있습니다.

컨테이너 자체가 없고 기존 데이터 볼륨이 남아 있다면 README의 `up -d app-db minio dashboard`로 재생성합니다. 볼륨까지 지워졌다면 재시작으로 자료를 복원할 수 없으므로 [복원 절차](backup-restore.md)를 확인합니다. Airflow와 Kubernetes는 이 보고서 조회에 필요하지 않습니다.

2026-10-23 접속 장애는 위 세 컨테이너가 모두 중지된 상태였습니다. 기존 컨테이너 시작 후 `/health`, `/ready`, PS_001 보고서 HTML·CSV·출처 JSON 모두 200 응답과 실제 보고서 본문 렌더를 확인했습니다. 데이터 재처리·이미지 재빌드·볼륨 삭제는 하지 않았습니다.

## 데이터 확인

1. `uv run solarops demo`로 합성 1주 보고서를 생성합니다.
2. `uv run solarops serve` 후 http://127.0.0.1:8501 에서 월간 리포트를 선택합니다.
3. 통합 보고서 본문에서 추정 kWh, 관측 슬롯 비율, 유효값 비율, 소스 보간율을 함께 봅니다. 관측 100%라도 NULL이 많을 수 있습니다. 일별 내역은 펼치고, 인쇄용 HTML은 별도 탭에서 엽니다.
4. 전체 현황에서 월·자료 구분을 선택하고, 발전소의 관측 보기로 이동해 전력(kW)/POA(W/m²)의 서로 다른 축과 품질 정보를 확인합니다. 시각은 보고서 설정 시간대이며 기본 UTC입니다.
5. 보고서 CSV와 계보 JSON을 내려받습니다. 출처/규칙/시간대/부분 기간 여부를 함께 전달합니다.

관측 차트의 전력은 실선, POA는 점선입니다. 끊김은 표시할 유효값이 없는 구간이며 0이 아닙니다. 아래 띠와 **빈 구간 시각 확인 (UTC)**에서 범위를 확인하세요. 관측 행은 있어도 필드가 비어 있을 수 있으므로 관측 슬롯 100%와 유효값 100%는 다릅니다. [실제 원본 대조 예](../benchmarks/interactions-20261023.md#차트의-끊김은-정상인가).

전체 실자료를 처리한 현재 작업 공간에는 PS_001~PS_051과 합성 DEMO_01이 있습니다. 2024년 4월 전체 현황의 공개 발전소는 해당 월에 자료가 있는 5개입니다. 보고서 자료 구분은 발전소 이름이 아닌 생성 당시 실제 출처로 결정합니다. `all-public`은 공개 자료만 포함합니다. 출처 파일을 읽지 못하는 예전 보고서는 전체 자료 목록에서 확인하고 저장소 상태를 점검합니다.

새 파일: 별도 폴더에서 `solarops source checksum`으로 확인 후 `solarops ingest`의 metadata/inverter/station 경로를 지정합니다. 공개 자료는 `--source-kind public`, 테스트는 synthetic. 데이터가 수정됐다면 새 버전을 주어야 합니다. 원본 파일을 직접 덮어써서 수정하지 않습니다.

v0.4.2의 `PUBLICATION_CONFLICT`는 배치 시작 후 같은 날짜의 active가 바뀌었다는 뜻입니다. 현재 결과와 입력 버전을 확인한 뒤 필요한 날짜만 재시도하세요. 이미 게시했다가 교체된 과거 버전으로 되돌리려면 `ingest` 또는 실행하는 `backfill`에 `--restore`를 명시합니다. 이 옵션도 동시성 검사는 유지하며 이전 run ID를 기록합니다. 실패한 날짜는 metadata와 함께 롤백되지만 배치 앞부분의 성공한 날짜는 유지됩니다.

상세 추적은 `uv run solarops inspect-runs --run-id <UUID>` 또는 기존 진단 API를 사용합니다. 새 실행에는 릴리스·Git 커밋·Airflow dag/run/task/attempt·Pod UID·처리 단계·행 수·오류·관련 시도를 기록합니다. [실제 실패/재시도 예](../benchmarks/integrity-v0.4.2.md). 환경이 주지 않은 필드는 비워 두며 경과시간만으로 프로세스 사망을 판단하지 않습니다.

실행 조사: [실행 이력](http://127.0.0.1:8502/?view=runs&run_plant=PS_001)에서 실행 단위·상태·정확한 발전소 ID로 좁힙니다. 전체 기간의 공개·합성 처리 이력을 조회하며 보고 월 필터와 별개입니다. 주소를 저장하면 페이지·선택한 상세까지 복원합니다. 상세의 날짜에서 하위 파티션으로 이동하고 **상위 작업 보기**로 돌아옵니다. 요약 건수는 상태 필터 적용 전이며, 과거 완료 기록이 현재 활성 결과임을 보장하지 않습니다.

상세의 **진단 조회하기**는 현재 게시 개수와 미완료 기록의 경과 시간을 읽습니다. 같은 날짜·계산 버전·시간대의 결과가 다른 실행에 연결되면 **현재 결과의 실행 보기**로 이동합니다. 시간 경과는 프로세스 중단의 확정 근거가 아닙니다. API는 `GET /api/v1/runs/{UUID}/diagnostics`이며 실행 상태를 변경하지 않습니다.

등록 월 안내: 빈 월의 **자료가 있는 월**은 현재 조직·보고 시간대·계산 버전·자료 구분으로 게시된 파티션을 기준으로 합니다(`GET /api/v1/periods`). 보고서는 **보고서가 있는 월**을 별도로 안내합니다. 본문 상단의 생성 기준 시각·입력/계산 버전으로 스냅샷 범위를 확인하세요.

기존 PostgreSQL의 발전소 조회 인덱스는 쓰기용 Catalog 초기화 시 추가됩니다. 읽기 전용 dashboard는 스키마를 바꾸지 않습니다. 기존 로컬 Compose에 새 코드를 적용한 뒤 필요하면 `docker compose --env-file .env -f infra/compose/compose.yaml exec dashboard python -c "from solarops.config import Settings; from solarops.storage.postgres import Catalog; Catalog(Settings()).engine.dispose()"`로 초기화합니다. 현재 로컬 DB에는 이미 반영했습니다. [실측·범위](../worklog/2026-10-23-usability.md#perf-02-17점).

보고서 월: `solarops report --period 2024-04 --plant PS_001 --source-kind public`. 생성된 보고서는 불변 UUID 경로를 가지며 최신 보고서 포인터만 변경됩니다. 이미 발행한 보고서는 후속 적재로 자동 수정되지 않으므로 월간 보고서를 다시 생성해야 합니다.

동시에 생성하면 스냅샷 조회 시작 시각이 더 새로운 보고서를 최신으로 유지합니다. 먼저 시작한 보고서가 늦게 끝나더라도 과거 UUID로 조회할 수 있습니다. 업로드/DB 커밋 실패는 이전 활성 보고서를 유지합니다.

조회 오류는 다음처럼 구분합니다. `/health`만 정상이고 `/ready`가503이면 catalog 스키마와 저장소 연결을 확인하세요. 산출물404는 파일 부재/접근 범위 문제, 무결성503은 저장한 SHA와 실제 바이트 불일치입니다. 원본을 덮어쓰거나 해시를 수정해 통과시키지 말고 파일과 로그를 보존한 뒤 [복원 절차](backup-restore.md)를 따릅니다. SHA가 없던 과거 산출물은 계속 조회되지만 소급 무결성 보장은 없습니다.

읽기 API는 프로세스 설정의 한 조직만 노출합니다. 사용자 입력으로 다른 org를 선택하는 기능은 없습니다. 127.0.0.1 이외 공개 배포는 인증/HTTPS/보존정책/백업/동의를 갖춘 별도 작업입니다.

정리 시에는 `make down-local`로 서비스를 중지합니다. raw/staging/PVC/볼륨을 자동 삭제하지 않습니다. 저장 공간이 부족하면 실제 사용 중인 active manifest를 확인하고 사용자 승인 후 정리 정책을 결정합니다.
