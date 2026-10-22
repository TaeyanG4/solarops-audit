# DAG와 명시적 재처리

| DAG | 역할 | 일정 |
|---|---|---|
| solarops_ingest_daily | 환경 확인 → 지정 발전소의 역사 구간 재처리/검증/공개 | 02:00 UTC, 초기 paused |
| solarops_quality_daily | 지정 발전소·자료 종류·기간의 활성 지표 조회 | 수동 |
| solarops_report_monthly | 지정 발전소·자료 종류·월 확인 → 계보 포함 보고서 공개 | 매월 2일 03:00 UTC, 초기 paused |
| solarops_backfill_manual | 명시 날짜 재생, 기본 dry_run=true | 수동 |

기본 `source_kind=synthetic`, `plant=DEMO_01`, `from_date=2024-04-01`, `to_date=2024-04-08`, `source_version=synthetic-v1`입니다. 공개 BR-PVGen은 `source_kind=public`, `plant=PS_001`처럼 지정합니다. 이미 전처리된 역사 자료이며 라이브 센서 수집이 아닙니다. 일정이 실행되어도 날짜 Params가 자동으로 오늘 날짜로 이동하지 않습니다. 정해진 구간을 반복 검증하려는 경우에만 unpause합니다.

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

배포 이미지 버전은 0.4.0입니다. 이후 코드 변경은 새 버전/digest로 배포하세요. Compose는 `docker compose --env-file .env -f infra/compose/compose.yaml --profile airflow build dashboard airflow-api` 후 해당 서비스를 `up -d`합니다. kind는 `bash scripts/ops/k8s-refresh.sh`로 이미지 로드와 롤아웃을 수행합니다. 완료 Pod/로그는 검증 증거로 남습니다.
