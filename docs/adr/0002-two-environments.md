# ADR 0002 — independent Compose and kind

수락. Compose는 app-db/minio와 별도 airflow-db를 사용합니다. kind도 solarops namespace에 각 서비스를 다시 배포하며 `*.solarops.svc.cluster.local`로 연결합니다. kind가 호스트 Compose 포트를 참조하지 않습니다.

kind 단일 노드 local-path는 RWX를 제공하지 않습니다. Airflow 로그에 사전 생성한 ReadWriteOnce PVC를 공유합니다. 최초 실패한 Pending PVC는 데이터를 삭제하지 않는 원칙에 따라 보존했습니다. 앱 작업은 별도 PVC와 MinIO를 사용합니다. 로컬 개발 PV는 백업이 아닙니다.

실제 PC 약 95GiB RAM, WSL 약 46.6GiB에서 병행 검증했습니다. 저메모리 환경은 두 스택을 번갈아 실행합니다.
