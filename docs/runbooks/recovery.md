# 실패와 복구

기본 커밋 단위는 한 조직/발전소/현지 날짜/시각대/계산 버전입니다. 파일 저장 후 PostgreSQL 트랜잭션에서 active manifest를 전환합니다. 로컬 SQLite도 같은 원자적 경계를 사용합니다.

**입력 검증 실패:** batch 등록 이후 실패는 실행 이력의 error_code와 해당 staging/quarantine.json을 확인합니다. 경로/기간/발전소 사전 검증이나 원본 등록 단계에서 중단되면 아직 run 또는 quarantine이 없을 수 있으므로 CLI 출력과 Airflow 태스크 로그를 먼저 봅니다. 원본을 보존한 채 새 파일·버전을 준비합니다. 동일키 상이값은 마지막 값으로 덮어쓰지 않습니다.

**중간 쓰기 또는 트랜잭션 실패:** 이전 active run_id는 유지됩니다. 같은 파일·버전·날짜로 재실행합니다. 불완전 staging은 자동 공개되지 않습니다. 장애를 재현하려면 `ingest --fail-at before_commit` 또는 `--fail-at during_commit`을 사용합니다.

**작업 Pod 실패:** `kubectl logs`와 Airflow 태스크 시도를 확인합니다. 기본 2회 재시도합니다. `python3 scripts/validation/k8s_fault.py`는 이 스크립트가 만든 합성 backfill 작업의 PID 1만 종료하며 데이터/PVC/Pod 객체를 삭제하지 않습니다. 실행 중인 다른 프로젝트나 시스템 프로세스는 건드리지 않습니다.

**여러 날짜 중 일부 실패:** 이미 커밋한 날짜는 유지됩니다. 실패 날짜만 `--from/--to`로 재실행하고 이전/이후 논리 해시를 비교합니다. 보고서는 새로 생성하기 전까지 이전 불변 산출물을 가리킵니다.

**배포 되돌리기:** `helm history airflow -n solarops`, 검토한 이전 revision에 `helm rollback airflow REVISION -n solarops`. 원본/마트 데이터 버전은 Helm 이미지 롤백과 별개입니다. 이전 파티션으로 되돌리려면 보존된 입력과 정확한 계산 버전으로 새 실행을 생성합니다. 운영 중 DB 직접 삭제/덮어쓰기 마이그레이션을 하지 않습니다.

**프로세스가 갑자기 죽은 실행:** pipeline_run이 running/validated로 남을 수 있습니다. 공개 결과 여부는 active manifest의 run_id로 확인합니다. 자동 TTL 삭제·강제 실패 처리기를 넣지 않았습니다. 운영자가 실행 상태/Pod 종료시각을 확인한 후 재시도합니다.

`uv run solarops inspect-runs --older-than-minutes 60 --limit 100 --offset 0`은 설정된 조직의 미완료 실행을 오래된 순으로 조회합니다. Compose는 `docker compose --env-file .env -f infra/compose/compose.yaml exec -T dashboard solarops inspect-runs`로 동일하게 조회합니다. `has_more`가 true이면 offset을 늘립니다. `active_partition_count`, `active_child_partition_count`, `child_status_counts`를 함께 확인합니다. 시간 누락·미래 시각도 검토 대상으로 표시합니다. SQLite는 기존 파일만 읽기 전용으로 열며 상태·스키마를 변경하지 않습니다.

`needs_review=true`는 실패 판정이 아닙니다. Airflow 실행/시도, 작업 프로세스나 Pod 상태·종료시각을 대조하고, 살아 있는 작업은 기다립니다. 종료가 확인되면 누락 날짜를 선택해 재실행하고 논리 해시와 보고서 계보를 확인합니다. 이 CLI는 작업을 강제 실패 처리하거나 삭제·재시도하지 않습니다.

kind는 재해복구 저장소가 아닙니다. 고객 도입 전 PostgreSQL dump + 객체 저장소 스냅샷을 별도 암호화 저장소에 보관하고 복원 시험을 해야 합니다. 이 프로젝트는 공개/합성 데이터만 가지고 있습니다.

## ONS 수집 실패

데이터 출처의 ONS 탭 또는 `solarops ons-status --period YYYY-MM`에서 최근 실패 코드와 마지막 성공을 따로 확인합니다. v0.5.2부터 새 실패에는 안전한 도메인 코드를 저장합니다. 과거 `ValueError` 기록은 소급 변경하지 않습니다.

| 코드 | 다음 확인 |
|---|---|
| `ONS_SOURCE_CONTRACT_CHANGED`, `ONS_SCHEMA_CHANGED` | 공식 metadata·헤더·라이선스와 adapter 계약 대조. 자료를 임의 변환해 통과시키지 않음 |
| `ONS_TIMESTAMP`, `ONS_ENTITY_ID`, `ONS_DUPLICATE_CONFLICT` | 보존 원본의 해당 계약과 충돌 확인. 정정 원문 확인 후 월 재시도 |
| `ONS_CURSOR_CONFLICT` | 다른 실행이 성공했는지 확인한 뒤 최신 cursor 기준으로 재시도 |
| `ONS_HTTP_404` | 월 파일의 실제 게시 여부 확인. 아직 없는 파일을 성공으로 표시하지 않음 |
| `ONS_HTTP_429`, `ONS_HTTP_5xx`, `ONS_TIMEOUT`, `ONS_NETWORK_ERROR` | 원천/연결 상태와 Airflow 재시도 간격 확인. 짧은 반복 다운로드 피하기 |
| `ONS_DOWNLOAD_LIMIT`, `ONS_INCOMPLETE_HTTP_RESPONSE`, `ONS_INCOMPLETE_ROW` | 원문 크기·응답 완전성 확인. 상한을 무조건 늘리지 않음 |
| `ONS_IO_ERROR`, `ONS_UNEXPECTED_ERROR` | 호스트 여유 공간·권한 및 제한된 로컬 태스크 로그 확인. 비밀값을 외부 문서에 복사하지 않음 |

성공 cursor가 남아 있다고 수집기가 현재 정상이라고 단정하지 않습니다. 프로세스 강제 종료로 남은 ONS `running` 기록도 Airflow/Pod와 대조해야 하며, 현재 자동 조정기는 없습니다. 삭제나 과거 성공 덮어쓰기 없이 새 실행으로 복구합니다.

## BR 입력·오류 코드와 범위 축소

새 실패의 `error_code`는 허용된 계약 코드 또는 `BR_INPUT_INVALID`(파싱/값), `BR_CATALOG_ERROR`(DB), `BR_OBJECT_STORE_ERROR`(S3), `BR_IO_ERROR`(파일), `BR_UNEXPECTED_ERROR`입니다. catalog·quarantine·CLI에 원문 값/접속 문자열을 복사하지 않습니다. 원인은 권한이 있는 로컬 원본/태스크 로그에서 확인하며 과거 오류 기록은 소급 변경하지 않습니다.

`SOURCE_RANGE_SHRINK`는 요청 안에 이미 게시한 날짜가 새 인버터 전체 관측 범위에서 빠졌다는 뜻입니다. 첫 날짜를 게시하기 전에 중단하고 이전 active를 유지합니다. 잘린 파일인지 먼저 조사하고 완전한 원본과 새 버전을 준비하거나 실제 지원 날짜로 요청을 좁힙니다. BR 날짜 철회 기능은 없으므로 DB/객체를 임의 삭제해 해결하지 않습니다. ONS는 별도 월 snapshot 철회 계약입니다.

## ONS running 기록이 오래 남을 때

`inspect-runs`는 BR `pipeline_run`용입니다. ONS는 **해당 저장소 환경**의 `solarops ons-status --period YYYY-MM`에서 `recent_runs`의 run_id·started_at·execution(dag_run_id, task_id, pod_name)을 확인합니다. Compose와 kind 저장소는 다르므로 Compose 결과로 kind 상태를 판단하지 않습니다.

kind의 WSL 터미널에서 실제 작업을 대조합니다(조회만 수행):

```bash
export PATH="$PWD/.tools:$PWD/.tools/linux-amd64:$PATH"
kubectl --kubeconfig artifacts/kubeconfig -n solarops exec airflow-scheduler-0 -c scheduler -- airflow dags list-runs solarops_ons_daily --state running --output json
# 기록에서 확인한 Pod 이름을 사용. Secret/환경 전체 출력은 불필요.
kubectl --kubeconfig artifacts/kubeconfig -n solarops get pod POD_NAME
kubectl --kubeconfig artifacts/kubeconfig -n solarops logs POD_NAME --tail=80
```

작업이 살아 있으면 기다립니다. 종료가 확인되면 기존 Airflow 재시도/수동 Trigger 또는 같은 환경의 월별 `ons-sync --period`를 사용합니다. 새 시도가 성공해도 과거 running을 성공으로 덮어쓰지 않습니다. 최근20회 밖 기록은 해당 DAG 실행 이력과 보존 로그로 추적하며, 자동 TTL/강제 실패 조정기는 없습니다.
