# 데이터 수집·일정·추가 방법

[프로젝트 홈](../../README.md) · [출처와 라이선스](../data-sources.md) · [아키텍처](../architecture/system.md) · [DAG 운영](../runbooks/dags.md)

**현재는 BR-PVGen V.1을 명시적으로 다운로드하고, 저장된 과거 CSV를 배치 처리하는 시스템입니다. 새 관측값을 주기적으로 가져오는 서비스는 실행하지 않습니다.** Airflow의 일정은 파일 다운로드가 아니라 지정한 과거 구간의 재처리와 보고서 생성을 담당합니다.

## 지금 자동으로 돌고 있는가

2026-10-23 13:11 KST에 확인·저장한 이 작업 PC의 상태입니다. 실행 상태는 이후 사용자의 시작·중지 조작에 따라 달라질 수 있습니다.

| 구간 | 구현된 실행 방식 | 확인한 상태 |
|---|---|---|
| 외부 파일 다운로드 | `solarops source fetch`를 명시적으로 호출 | 정기 다운로드 DAG 없음 |
| Compose 분석 서비스 | PostgreSQL·MinIO·대시보드 3개 컨테이너 | 실행 중. 화면을 열어도 수집·재처리하지 않음 |
| Compose Airflow | 별도 API·scheduler·dag-processor·메타 DB | 4개 모두 중지 |
| kind Airflow | LocalExecutor가 KPO 작업 Pod를 호출 | 서비스 Pod 6개 Ready, DAG 4개 모두 paused |
| kind 진행 중인 배치 | Airflow 메타 DB의 `dag_run` 조회 | `running` / `queued` 0건 |

Airflow가 켜져 있다는 사실만으로 자동 적재 중이라고 판단하면 안 됩니다. 과거 공개/합성 DAG의 성공 이력과 현재 스케줄 활성 여부도 구분합니다. [확인 명령과 결과](../worklog/2026-10-23-data-architecture.md).

## 수집에서 화면까지

1. **목록 확인:** 고정된 [Zenodo record 21511487](https://zenodo.org/records/21511487)의 API에서 파일 크기·다운로드 URL·게시 MD5를 읽습니다. 최신 record를 자동 탐색하지 않습니다.
2. **다운로드:** 허용된 설명·metadata·인버터 ZIP·기상 ZIP만 받습니다. 1MB 초과 파일은 `--allow-large`가 필요하고 파일당 상한은 400,000,000바이트입니다. 임시 파일의 크기와 MD5를 확인한 뒤 정식 파일명으로 전환합니다.
3. **보존·압축 해제:** SHA-256·출처·버전·라이선스 manifest를 남깁니다. ZIP 경로 이탈·심볼릭 링크·과도한 팽창을 거부하며 CSV만 추출합니다. 기존 원본이나 추출 파일의 내용이 다르면 덮어쓰지 않고 중단합니다.
4. **등록·처리:** `ingest` / `replay`가 원본 사본을 저장하고 그 사본을 읽습니다. 스키마·UTC·15분 간격·중복을 검사하고 DuckDB로 정렬, 하루씩 분석해 Parquet·품질·추정 에너지·계보를 생성합니다.
5. **게시·조회:** 검증된 일별 결과만 DB 트랜잭션으로 활성화합니다. 대시보드는 활성 결과를 조회하며 보고서는 별도 명령으로 생성한 시점의 자료를 고정합니다.

여기서 **다운로드**, **처리**, **보고서 발행**은 별도 작업입니다. 재처리는 동일한 파일을 다시 계산하는 것이며 새로운 관측 데이터의 수집 실적이 아닙니다. 원본 보간·표본 수를 보존하고 새 보간값을 만들지 않습니다. 계산 결과는 계량기 실측 전력량이 아닌 **추정 에너지**입니다.

구현: [다운로더](../../src/solarops/acquisition/brpvgen.py) · [공통 CLI](../../src/solarops/cli.py) · [재처리](../../src/solarops/replay.py) · [파이프라인](../../src/solarops/pipeline.py).

## 코드에 정의된 일정

| DAG | 일정 UTC / 한국 시각 | 실제 하는 일 |
|---|---|---|
| `solarops_ingest_daily` | 매일 02:00 / 11:00 | 환경 확인 후 지정 발전소·기간 `replay` |
| `solarops_quality_daily` | 수동 | 이미 게시된 지표 `analyze`; 외부 수집이나 독립적인 전체 품질 재검사 아님 |
| `solarops_report_monthly` | 매월 2일 03:00 / 12:00 | 지정 월 `analyze` 후 `report` |
| `solarops_backfill_manual` | 수동, 기본 dry-run | 최대 31일의 명시적 과거 구간 재처리 |

네 DAG는 처음부터 paused로 생성됩니다. `catchup=False`, DAG별 동시 실행 1개, 실패 재시도 2회이며 서로 다른 DAG 사이의 자동 연결은 없습니다. 일별 적재가 끝나면 품질/보고서 DAG가 자동 발동하는 구조가 아닙니다.

기본 Params는 **합성 DEMO_01 / 2024-04-01 이상~2024-04-08 미만 / synthetic-v1 / 보고 월 2024-04**입니다. 날짜나 월을 `data_interval`에서 계산하지 않으므로 **unpause만 하면 같은 역사 구간을 반복**합니다. `source_kind=public`도 미리 준비한 BR-PVGen 파일을 읽으며 신규 파일을 내려받지 않습니다. [정확한 Params와 운영 절차](../runbooks/dags.md).

## 데이터를 더 추가할 수 있는가

**가능하지만, 현재 지원 범위 안의 추가 처리와 새로운 출처 연동은 작업량이 다릅니다.**

| 추가하려는 자료 | 현재 가능한 범위 | 필요한 작업 |
|---|---|---|
| 현재 V.1의 다른 발전소·월 | 같은 계약의 파일을 선택해 처리 가능 | 파일 준비 → 구간 계획 → 실제 처리 → 보고서 생성 |
| V.1 전체 기간 | 이 PC의 Compose에는 이미 51개 발전소·12,572개 일별 파티션 처리 완료 | 먼저 월/자료 필터 확인. 2024년 4월의 5개는 해당 월에 자료가 있는 발전소 수 |
| BR-PVGen 새 배포 버전 | 자동 발견·다운로드 미지원 | 새 record·DOI·라이선스·스키마 확인, 수집기와 계보 처리 수정, 별도 원본 폴더·버전으로 적재 |
| 다른 공개 태양광·기상 CSV/API | 현재 전용 입력 경로로 바로 지원하지 않음 | 출처별 adapter·계보 등록, 단위/시간대/간격·ID 대응과 품질 계약 검증 |
| 실제 고객·SCADA·계량기 | 현재 연결·업로드 없음 | 이용 권한, 조직·인증/권한, 별도 입력 계약·보안·운영 범위부터 확정 |
| 신규 관측값 정기 수집 | 현재 미구현 | API/파일 connector, 수집 위치 기록, 지연/수정 자료 재처리, 일정 연결·장애 관측 |

현재 `source_kind`는 `public` / `synthetic`만 받으며, `public`은 `demo` 조직의 BR-PVGen DOI·CC BY 4.0으로 기록됩니다. **컬럼 이름만 맞춘 타 출처 CSV에 `--source-kind public`을 붙이면 잘못된 계보가 됩니다.** `--source-version`은 로컬 입력 바이트의 버전 이름이며 새로운 출처나 DOI를 등록하는 옵션이 아닙니다. 다른 원천은 이 부분까지 확장한 뒤 추가해야 합니다.

특히 5분 전력, 누적 kWh 계량값, 15분 평균 W는 서로 다릅니다. 현재 15분 전력 산식을 그대로 적용하지 않습니다. 원본 보간/표본 수가 없는 자료도 임의로 정상 관측으로 표시하지 않습니다. [입력·계산 계약](../data-contract.md).

## 현재 자료를 처리하는 명령

모든 명령은 저장소 루트 기준입니다. 아래는 필요할 때 실행할 절차이며, 이번 문서 작업에서 다운로드·실제 재처리·새 보고서 발행을 실행하지 않았습니다.

### 1. 원본 준비

```text
uv run solarops source inspect
uv run solarops source fetch --allow-large --files Readme.txt BR-PVGen_metadata.csv BR-PVGen_inverter.zip BR-PVGen_meteorological.zip
uv run solarops source extract data/source/BR-PVGen_inverter.zip data/source/inverter
uv run solarops source extract data/source/BR-PVGen_meteorological.zip data/source/station
```

이미 같은 파일이 있으면 checksum을 확인해 재사용합니다. 다른 파일은 새 폴더에 보존해야 하며 기존 원본을 삭제해 충돌을 우회하지 않습니다. `source fetch --destination`과 `SOLAROPS_SOURCE_DIR`은 별도 설정이므로 사용자 지정 경로는 둘 다 맞춰야 합니다. 기본 `source fetch`는 설명과 metadata만 받습니다.

### 2. 네이티브 환경에서 구간 계획

```text
uv run solarops replay --source-kind public --plant PS_001 --from 2024-04-03 --to 2024-04-04 --source-version brpvgen-v1
```

기본 dry-run이며 2026-10-23에 위 명령의 경로·관측 범위 확인 성공을 검증했습니다. dry-run은 전체 값·중복·버전 충돌까지 검증하지 않습니다. 실제 처리는 같은 명령 끝에 `--dry-run false`를 추가합니다. 기본 설정에서는 네이티브 SQLite/파일에 기록되어 **Compose 8502 화면은 바뀌지 않습니다**. `.env`도 네이티브 CLI가 자동으로 읽지 않습니다.

기간은 `--from` 포함 / `--to` 미포함, 보고서 시간대의 날짜(기본 UTC)입니다. `replay`는 1~31일, 파일 경로를 직접 지정하는 `ingest`는 최대 500일입니다. `ingest`는 dry-run이 아니므로 계획 확인에는 `replay`를 사용합니다.

### 3. Compose 8502용 처리와 보고서

PostgreSQL·MinIO가 준비되어 있고 호스트 `data/source`가 Compose에 마운트된 환경에서 실행합니다. 기본 서비스 시작은 [설치 안내](setup.md)를 따릅니다.

```text
docker compose --env-file .env -f infra/compose/compose.yaml --profile jobs run --no-deps worker replay --source-kind public --plant PS_001 --from 2024-04-03 --to 2024-04-04 --source-version brpvgen-v1
```

이 명령도 계획만 확인합니다. 실제 처리가 필요할 때 `--dry-run false`를 추가합니다. 다운로드는 하지 않으며 실행용 컨테이너는 종료 후 보존됩니다. worker의 `/source`는 읽기 전용 호스트 원본입니다. dashboard 컨테이너에는 원본 마운트가 없으므로 dashboard에서 `replay`하지 않습니다.

필요한 날짜를 처리한 다음 같은 서비스 저장소의 월간 보고서를 발행합니다:

```text
docker compose --env-file .env -f infra/compose/compose.yaml exec -T dashboard solarops report --period 2024-04 --plant PS_001 --source-kind public
```

보고서는 기존 UUID를 덮어쓰지 않고 새로 생성합니다. 하루만 처리한 월은 부분 기간 보고서이며, 입력 파일의 전체 기간이 자동으로 적재되지는 않습니다. 최신 dashboard 코드는 보고서 선택 범위를 기록하지만 이전 Airflow/kind worker 이미지의 보고서는 해당 필드가 없어 근거 비교가 `unavailable`일 수 있습니다. 이미지 갱신은 별도 배포 작업입니다.

kind는 독립 DB/MinIO를 사용합니다. 원본을 PVC에 준비하고 해당 환경의 DAG를 실행해야 하며 Compose 결과와 자동 동기화하지 않습니다. [파일 준비·Params](../runbooks/dags.md), [배포 구조](../architecture/system.md).

## 정기 수집으로 확장할 때의 순서

1. 실제 갱신되는 원천과 이용 조건, 시간 간격·단위·조직 범위를 정합니다. 고정된 역사 ZIP을 매일 다시 받는 것으로는 새 관측값이 생기지 않습니다.
2. 출처 ID·URL·라이선스를 입력별로 보존하는 등록 경로와 adapter를 만듭니다. 기존 BR-PVGen/합성 표기를 타 출처에 재사용하지 않습니다.
3. 마지막 성공 수집 위치와 바이트/버전을 기록하고, 중복·지연 도착·수정 자료의 재처리 범위를 정합니다. 실패한 수집에서 성공 위치를 앞당기지 않습니다.
4. 수집 완료 후 검증·일별 게시·보고서를 명시적 의존성으로 연결하고, 대상 기간을 스케줄 구간에서 계산합니다. 그 뒤에만 일정 활성화와 재시도/실패 보존을 검증합니다.

이 항목들은 확장 설계이며 현재 완료된 기능이 아닙니다. 현재 입력 규모에서는 파일/API 배치로 시작할 수 있으며, 실시간 요구나 처리량 근거 없이 스트리밍 도구부터 추가할 필요는 없습니다.
