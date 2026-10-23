# DAG와 명시적 재처리

[수집 주기·데이터 추가](../guides/data-ingestion.md) · [아키텍처](../architecture/system.md)

BR-PVGen의 기존4개 DAG는 저장된 역사 자료를 재처리합니다. v0.5.0에는 실제 ONS 갱신 원천을 확인하는1개 DAG와 수동 공개 성능시험2개 DAG가 추가되었습니다. 총7개이며 모두 최초 생성 시 paused입니다. 실제 활성화 상태와 검증 근거는 [작업 기록](../worklog/2026-10-23-incremental.md)을 확인합니다.

| DAG | 역할 | 일정 |
|---|---|---|
| solarops_ingest_daily | 환경 확인 → 지정 발전소의 역사 구간 재처리/검증/공개 | 02:00 UTC, 초기 paused |
| solarops_quality_daily | 지정 발전소·자료 종류·기간의 활성 지표 조회 | 수동 |
| solarops_report_monthly | 지정 발전소·자료 종류·월 확인 → 계보 포함 보고서 공개 | 매월 2일 03:00 UTC, 초기 paused |
| solarops_backfill_manual | 명시 날짜 재생, 기본 dry_run=true | 수동 |
| solarops_ons_daily | ONS 이전/현재 월 조건부 다운로드·변경 날짜 게시 | 매일05:00 UTC /14:00 KST |
| solarops_public_benchmark_1 / _2 | 같은 공개4일, 동시1/2 비교; 별도 DB·버킷 필수 | 수동, KPO 전용 |

기존 BR-PVGen4개 DAG의 기본 `source_kind=synthetic`, `plant=DEMO_01`, `from_date=2024-04-01`, `to_date=2024-04-08`, `source_version=synthetic-v1`입니다. 공개 BR-PVGen은 `source_kind=public`, `plant=PS_001`처럼 지정합니다. 이미 전처리된 역사 자료이며 라이브 센서 수집이 아닙니다. 일정이 실행되어도 날짜 Params가 자동으로 오늘 날짜로 이동하지 않습니다. 정해진 구간을 반복 검증하려는 경우에만 unpause합니다.

보고 월 `period`도 기본 `2024-04`로 고정됩니다. DAG 사이에 자동 실행 의존성은 없고, 품질 DAG의 `analyze`는 게시된 지표를 조회하는 명령입니다. 이름의 `daily`가 정기 원본 수집이나 별도의 전체 품질 재검사를 뜻하지 않습니다. 한국 시각은 일별 11:00, 월간 매월 2일 12:00입니다.

## 공개 자료 준비

`make download-full`로 별도 다운로드/압축 해제를 수행합니다. DAG 실행과 설치/테스트는 자동 다운로드하지 않습니다. 기본 레이아웃:

```text
data/source/
  BR-PVGen_metadata.csv
  inverter/BR-PVGen_inverter/PS_001.csv
  station/BR-PVGen_meteorological/PS_001.csv
```

로컬 CLI는 `SOLAROPS_SOURCE_DIR`(기본 `data/source`)를 읽습니다. Compose는 이 폴더를 `/source`에 읽기 전용으로 마운트합니다. 다른 호스트 경로는 `.env`의 `SOLAROPS_SOURCE_HOST_DIR`에 절대 경로를 설정한 뒤 Airflow 서비스를 다시 실행합니다. 컨테이너 내부 `SOLAROPS_SOURCE_DIR`는 `/source`로 고정됩니다.

kind에서는 KPO 작업이 기존 `solarops-data` PVC의 `/data/source`를 읽습니다. 다운로드한 자료 중 한 발전소만 복사할 수 있습니다:

```bash
python3 scripts/ops/k8s-stage-public.py --plant PS_001
```

이 도구는 metadata/인버터/기상 3개 파일을 SHA-256으로 검증하고 기존 파일이 동일하면 재사용합니다. 내용이 다르면 중단하며 덮어쓰지 않습니다. 전송 중 파일은 `/data/source-staging`에 남기고 검증된 파일만 원자적으로 연결합니다. 도움 Pod는 종료 후 보존되며 다운로드·기존 데이터 삭제는 하지 않습니다. 수정된 원본으로 교체해야 할 때는 별도 소스 루트/PVC와 명시 버전을 준비합니다.

## 계획 확인과 실행

```bash
# 기본 dry-run: 파일/발전소/관측 범위 확인, DB·Parquet·보고서는 생성하지 않음
uv run solarops replay --source-kind public --plant PS_001 \
  --from 2024-04-03 --to 2024-04-04 --source-version brpvgen-v1
# 같은 명령에 --dry-run false를 추가하면 실제 처리
```

계획 확인은 파일 존재·경로·metadata·인버터의 관측 범위를 확인합니다. 전체 값·중복·소스 버전 충돌 검증은 실제 처리에서 수행합니다. 계획 확인 성공이 전체 품질 검증 성공을 뜻하지 않습니다.

Airflow UI Trigger의 JSON 예시:

```json
{
  "source_kind": "public",
  "plant": "PS_001",
  "from_date": "2024-04-03",
  "to_date": "2024-04-04",
  "source_version": "brpvgen-v1",
  "period": "2024-04",
  "dry_run": "true"
}
```

`solarops_backfill_manual`에서 계획을 확인한 뒤 `dry_run="false"`로 실제 처리합니다. `solarops_ingest_daily` 기본값은 `false`입니다. 품질/보고서 DAG는 dry_run 파라미터를 사용하지 않으며, 보고서 DAG의 확인 단계와 생성 단계는 모두 `period`의 같은 월을 사용합니다. 합성과 공개 자료가 섞이지 않도록 `plant`와 `source_kind`가 모든 단계에 전달됩니다. 입력에 해당 기간이 전혀 없으면 성공으로 처리하지 않습니다.

Airflow 3.3 CLI: `airflow dags list-runs DAG_ID --output json` (dag ID는 위치 인수).

```bash
# Compose의 정상/재시도/실제 백필/품질/보고서 검증; 끝난 DAG는 pause
uv run python scripts/validation/airflow_checks.py --mode compose
# kind
python3 scripts/validation/airflow_checks.py --mode k8s
# 공개 PS_001 계획/처리/백필/품질/보고서 실제 실행
uv run python scripts/validation/airflow_checks.py --mode compose --source-kind public \
  --plant PS_001 --from 2024-04-03 --to 2024-04-04 \
  --source-version brpvgen-v1 --period 2024-04
# kind에서도 소스 복사 후 --mode k8s로 같은 검증 가능
```

UI Params의 날짜는 ISO date, 버전은 경로 안전 문자로 제한합니다. 실행 CLI에서 최대 31일을 다시 확인합니다. Backfill의 `dry_run=false`를 명시해야 실제 처리합니다. 공개 자료 직접 CLI ingest는 최대 500일을 지원하고, 무제한 날짜 처리는 거부합니다.

`fault_marker`와 `test_delay`는 합성 자료의 장애 시연에만 적용됩니다. `fault_marker`가 새 이름이면 첫 실행에서 DB 커밋 도중 예외를 발생시키고, 다음 재시도에서 같은 결과를 정상 공개합니다. 동일 marker는 다시 실패시키지 않습니다. 기존 marker를 삭제하지 말고 새 이름을 사용합니다.

dashboard·worker·Airflow·KPO는 같은 릴리스 선언을 사용합니다. 실제 배포 상태와 이미지 식별자는 [현재 handoff](../../handoff.md)에서 확인합니다. [릴리스 명세](../../src/solarops/release.json)를 변경하고 `uv run python scripts/release/release.py sync`, `uv lock`, `check`를 실행한 뒤 구현을 커밋합니다. `uv run python scripts/release/release.py build`는 두 이미지를 빌드하고 커밋/이미지 ID를 기록합니다. [0.4.2 당시 증거](../releases/0.4.2.json). kind의 `bash scripts/ops/k8s-refresh.sh`는 이미지 로드와 롤아웃을 수행하므로 상태 조회용으로 실행하지 않습니다. 완료 Pod/로그·과거 보고서는 보존하며 소급 변경하지 않습니다.

## ONS 정기 수집 켜기/끄기

kind가 켜져 있을 때 WSL에서 실행합니다. pause는 다음 스케줄을 중단하며 이미 실행 중인 Pod를 강제 종료하지 않습니다.

```bash
kubectl --kubeconfig artifacts/kubeconfig -n solarops exec airflow-scheduler-0 -c scheduler -- airflow dags unpause solarops_ons_daily
kubectl --kubeconfig artifacts/kubeconfig -n solarops exec airflow-scheduler-0 -c scheduler -- airflow dags pause solarops_ons_daily
```

기준일 override는 Trigger JSON `{"as_of":"2026-10-23"}`입니다. 생략하면 스케줄의 `data_interval_end`를 사용합니다. 현재/이전 월 이외의 오래된 정정은 공통 CLI `solarops ons-sync --period YYYY-MM`으로 처리합니다. 오류는 월별 성공 cursor를 전진시키지 않습니다. [입력·라이선스·시간대 한계](../ons-source-contract.md).

## 공개 DAG 병렬 측정

```text
uv run python scripts/validation/k8s_benchmark.py
```

Python3.12·실행 중인 kind/Airflow·일치하는 worker 이미지·PVC의 PS_001 원본이 필요합니다. Windows에서는 Ubuntu-22.04의 kubectl을 사용합니다. runner는 매번 별도 DB/버킷을 만들고 benchmark 전용 Secret을 설정한 뒤4일을 직렬/동시2로 실행합니다. 종료 후 두 DAG는 paused, probe는 종료되며 DB·객체·Pod·로그는 보존합니다. 기존 demo 게시를 쓰거나 원본을 다운로드하지 않습니다.

출력은 `artifacts/dag-benchmark-<시각>/`이며 실제 DAG시간·workerCPU/RSS·DB통계 delta·S3새 객체수/바이트·DB/MinIO Pod CPU/샘플 메모리·논리hash를 기록합니다. S3수치는 요청 지연시간이 아니며, 캐시/시작 비용을 포함한 단일 호스트 시험입니다. 로컬 기준은 오류0·hash동일·workerRSS<2GiB·10분 이내, 병렬 권고는15% 이상 시간 감소입니다.
