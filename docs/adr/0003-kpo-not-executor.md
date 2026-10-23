# ADR 0003 — LocalExecutor and KPO

수락. Airflow 3.3.2 / cncf-kubernetes provider 10.24.0 / chart 1.22.0. LocalExecutor가 DAG 태스크를 스케줄링하고 KPO가 [현재 릴리스 명세](../../src/solarops/release.json)의 worker 이미지로 작업 Pod를 생성합니다. 최초 결정 당시 태그는0.4.0이며 현재 버전/실행 증거는 [릴리스·배포 기록](../../handoff.md)을 따릅니다. Compose에서는 동일한 CLI를 격리된 Python venv에서 subprocess로 실행합니다.

Airflow 3.3의 DagBag 서명이 변경되어 최신 `airflow.dag_processing.dagbag`를 사용합니다. DAG 파일은 safe-mode 검색 키워드를 포함하고 helper 모듈 경로를 명시했습니다. 데이터/분석/공개는 트랜잭션 경계 유지와 과도한 왕복 방지를 위해 하나의 CLI 태스크로 묶었습니다. 단계별 함수는 앱에서 구현하며 DAG에서 업무 계산을 복제하지 않습니다.

XCom에 DataFrame이나 결과 배열을 싣지 않습니다. retry 2회, 지수 backoff, 작업 20분/Pod 15분 제한, max_active_runs=1, catchup=False. Backfill은 기본 dry-run, 최대 31일. 기본 DAG는 명시적으로 합성 역사 재생이며 신규 라이브 데이터라고 표현하지 않습니다.

Pod는 non-root/read-only rootfs, CPU 250m/2cores, RAM 512Mi/2Gi. 완료/실패 Pod를 남겨 조사할 수 있게 했으며 자동 영구 삭제를 하지 않습니다. 실 배포에서는 이미지 digest와 제한된 S3 사용자로 강화해야 합니다.
