# DAG와 명시적 재처리

| DAG | 역할 | 일정 |
|---|---|---|
| solarops_ingest_daily | 환경 확인 → 합성 역사 구간 재생/검증/공개 | 02:00 UTC, 초기 paused |
| solarops_quality_daily | 활성 파티션의 검증된 지표 조회 | 수동 |
| solarops_report_monthly | 활성 데이터 확인 → 계보 포함 보고서 공개 | 매월 2일 03:00 UTC, 초기 paused |
| solarops_backfill_manual | 명시 날짜 재생, 기본 dry_run=true | 수동 |

기본 `from_date=2024-04-01`, `to_date=2024-04-08`, `source_version=synthetic-v1`입니다. 이미 전처리된 공개 자료나 합성 자료를 실제 라이브 센서 수집으로 표시하지 않습니다. 제공 DAG는 합성 데모용 재생입니다. 실제 BR-PVGen 입력은 CLI와 full_dataset.py의 명시 경로로 처리합니다. 향후 고객 파일 도착 모드는 승인된 어댑터와 연결해야 합니다.

Airflow 3.3 CLI: `airflow dags list-runs DAG_ID --output json` (dag ID는 위치 인수).

```bash
# Compose의 정상/재시도/실제 백필/품질/보고서 검증; 끝난 DAG는 pause
uv run python scripts/airflow_checks.py --mode compose
# kind
python3 scripts/airflow_checks.py --mode k8s
```

UI Params의 날짜는 ISO date, 버전은 경로 안전 문자로 제한합니다. 실행 CLI에서 최대 31일을 다시 확인합니다. Backfill의 `dry_run=false`를 명시해야 실제 처리합니다. 공개 자료 직접 CLI ingest는 최대 500일을 지원하고, 무제한 날짜 처리는 거부합니다.

`fault_marker`와 `test_delay`는 장애 시연 전용입니다. `fault_marker`가 새 이름이면 첫 실행에서 DB 커밋 도중 예외를 발생시키고, 다음 재시도에서 같은 결과를 정상 공개합니다. 동일 marker는 다시 실패시키지 않습니다. 기존 marker를 삭제하지 말고 새 이름을 사용합니다.

배포 이미지 버전은 0.1.0입니다. 이후 코드 변경은 새 버전/digest로 배포하세요. 초기 개발 중 이미지를 재빌드한 경우 `kind load docker-image`와 해당 워크로드 롤아웃으로 반영합니다. 완료 Pod/로그는 검증 증거로 남습니다.
