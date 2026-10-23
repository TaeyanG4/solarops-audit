# 실행 보조 스크립트

[프로젝트 홈](../README.md) · [설치](../docs/guides/setup.md) · [개발 검사](../CONTRIBUTING.md)

모든 명령은 **저장소 루트**에서 실행합니다. Python 도구는 `uv run python scripts/<분류>/<파일>.py`, 셸 도구는 Linux/WSL의 `bash scripts/<분류>/<파일>.sh`로 실행합니다. 기존 평면 경로는 v0.3.1에서 이동했습니다. Makefile과 문서·CI는 새 경로를 사용합니다.

| 폴더 | 파일 / 역할 | 실행 영향 |
|---|---|---|
| `ops/` | `bootstrap.py`, `bootstrap-local.sh` | 없는 `.env`의 무작위 secret 생성, 로컬 이미지 빌드·서비스 기동 |
| `ops/` | `admin.ps1 start/status/stop` | Windows의 별도 8504 관리 서버를 백그라운드 실행/확인/종료. 컨테이너는 UI에서 조작 |
| `ops/` | `install-k8s-tools.sh`, `k8s-bootstrap.sh` | 도구 다운로드와 로컬 kind 클러스터 준비 |
| `ops/` | `k8s-deploy.sh`, `k8s-refresh.sh`, `k8s-secrets.py` | 배포/롤아웃, ignored 영역의 비밀 설정 생성 |
| `ops/` | `k8s-stage-public.py` | 선택 발전소 입력을 PVC에 checksum 확인 후 복사; 덮어쓰기 금지 |
| `ops/` | `k8s-smoke.sh` | DAG 검증 실행을 포함한 서비스 확인 |
| `validation/` | `check_docs.py`, `validate_dags.py` | 링크·스크립트 경로·원본 기획 checksum 검사 / Airflow 이미지 내 DAG 검사 |
| `validation/` | `service-test.py`, `airflow_checks.py` | 실제 서비스에 격리된 테스트 자료 생성 / 시나리오 DAG 실행 |
| `validation/` | `benchmark_dashboard.py`, `verify_catalogs.py` | HTTP 조회 측정 / 기존 native·서비스 결과 대조 |
| `validation/` | `overview_browser.py` | 실행 중인 공개·합성 데모를 Agent Browser로 읽기 검증. null/오류 fixture는 테스트 브라우저에만 주입, 출력은 새 폴더 |
| `validation/` | `workspace_browser.py --output <새 폴더>` | 7개 탐색·보고서·선택창·8504 검증. `--lifecycle`을 명시하면 실제 SolarOps 전체 중지·복구하므로 처리 작업이 없는 시점에만 실행 |
| `validation/` | `interaction_browser.py --output <새 폴더>` | 준비된8502/8504의 선택창 스크롤·관리 직접 탐색/탭·관측 빈값을 3너비에서 읽기 검증. 관리 요청 제출 없음; fixture는 브라우저에만 주입 |
| `validation/` | `interaction_browser.py --selectors-only --output <새 폴더>` | 열린 목록의 페이지 스크롤·버튼 정렬·크기 변경·내부 스크롤·키보드·닫힘만 검증 |
| `validation/` | `compare_calculations.py` | 보존한 v1 기준과 v2 전체 일별 지표·원본 SHA·표본 시계열 비교 |
| `validation/` | `backup_restore_drill.py` | 새 합성 SQLite/파일의 별도 경로 복원·해시·API·재처리 시험; 실제 서비스 백업 도구는 아님 |
| `validation/` | `service_restore_drill.py` | 합성 전용 DB/버킷 복원. `--isolated-target`이면 별도 PostgreSQL·MinIO 컨테이너에 복원하고 시험 후 중지; 자원·증거 보존 |
| `validation/` | `k8s_benchmark.py`, `k8s_fault.py` | 합성 작업 생성 / **이 도구가 시작한 작업 프로세스 종료** 후 재시도 확인 |
| `demo/` | `portfolio_demo.py` | 독립 새 폴더에 합성 정상·실패·복구 증거, 선택적 8503 UI |
| `demo/` | `pilot_price.py` | 입력 가정에 따른 가격/원가 산술; 실제 매출 예측 아님 |
| `data/` | `full_dataset.py` | 이미 받은 공개 51개 발전소를 처리; 부하·저장공간 사용 큼 |
| `release/` | `package_source.py` | 버전을 읽어 소스 ZIP+SHA-256 목록 생성; 기존 ZIP 보존 |
| `release/` | `release.py check/sync/build` | 단일 릴리스 명세와 Compose/Helm 선언 대조·동기화, 커밋된 소스로 두 이미지 빌드·커밋/이미지 ID 기록 |
| `archive/` | `finalize_ui.py` | v0.1 일회성 텍스트 교체 이력. 현재 소스에 실행하지 않도록 즉시 종료 |

새 스크립트는 목적에 맞는 폴더에 두고 도메인 로직은 `src/solarops/`의 공통 함수를 호출합니다. 실행 결과는 `artifacts/`나 `data/` 아래 별도 경로에 기록합니다. 원본 기획의 `docs/plan/scripts/`는 이 구조 개편과 무관하게 그대로 보존합니다.
