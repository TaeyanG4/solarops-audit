# 실패와 복구

기본 커밋 단위는 한 조직/발전소/현지 날짜/시각대/계산 버전입니다. 파일 저장 후 PostgreSQL 트랜잭션에서 active manifest를 전환합니다. 로컬 SQLite도 같은 원자적 경계를 사용합니다.

**입력 검증 실패:** batch 등록 이후 실패는 실행 이력의 error_code와 해당 staging/quarantine.json을 확인합니다. 경로/기간/발전소 사전 검증이나 원본 등록 단계에서 중단되면 아직 run 또는 quarantine이 없을 수 있으므로 CLI 출력과 Airflow 태스크 로그를 먼저 봅니다. 원본을 보존한 채 새 파일·버전을 준비합니다. 동일키 상이값은 마지막 값으로 덮어쓰지 않습니다.

**중간 쓰기 또는 트랜잭션 실패:** 이전 active run_id는 유지됩니다. 같은 파일·버전·날짜로 재실행합니다. 불완전 staging은 자동 공개되지 않습니다. 장애를 재현하려면 `ingest --fail-at before_commit` 또는 `--fail-at during_commit`을 사용합니다.

**작업 Pod 실패:** `kubectl logs`와 Airflow 태스크 시도를 확인합니다. 기본 2회 재시도합니다. `python3 scripts/validation/k8s_fault.py`는 이 스크립트가 만든 합성 backfill 작업의 PID 1만 종료하며 데이터/PVC/Pod 객체를 삭제하지 않습니다. 실행 중인 다른 프로젝트나 시스템 프로세스는 건드리지 않습니다.

**여러 날짜 중 일부 실패:** 이미 커밋한 날짜는 유지됩니다. 실패 날짜만 `--from/--to`로 재실행하고 이전/이후 논리 해시를 비교합니다. 보고서는 새로 생성하기 전까지 이전 불변 산출물을 가리킵니다.

**배포 되돌리기:** `helm history airflow -n solarops`, 검토한 이전 revision에 `helm rollback airflow REVISION -n solarops`. 원본/마트 데이터 버전은 Helm 이미지 롤백과 별개입니다. 이전 파티션으로 되돌리려면 보존된 입력과 정확한 계산 버전으로 새 실행을 생성합니다. 운영 중 DB 직접 삭제/덮어쓰기 마이그레이션을 하지 않습니다.

**프로세스가 갑자기 죽은 실행:** pipeline_run이 running/validated로 남을 수 있습니다. 공개 결과 여부는 active manifest의 run_id로 확인합니다. 자동 TTL 삭제·강제 실패 처리기를 넣지 않았습니다. 운영자가 실행 상태/Pod 종료시각을 확인한 후 재시도합니다.

kind는 재해복구 저장소가 아닙니다. 고객 도입 전 PostgreSQL dump + 객체 저장소 스냅샷을 별도 암호화 저장소에 보관하고 복원 시험을 해야 합니다. 이 프로젝트는 공개/합성 데이터만 가지고 있습니다.
