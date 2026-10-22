# v0.3.1 문서·구조·API 유지보수 검증

기준: 2026-10-22. [현재 상태](../IMPLEMENTATION_STATUS.md) · [변경 이력](../../CHANGELOG.md)

이번 변경은 API 입력 계약과 보고서 출처 필터, 소스 패키징, 스크립트 위치와 문서입니다. 계산 규칙 `energy-interval-v1`과 기존 파티션·보고서·원본 기획은 보존했습니다. 51개 전체 재처리나 고장 탐지 평가를 새로 수행한 릴리스가 아닙니다.

## 새 회귀 범위

- 잘못된 ISO 날짜, 잘못된 실제 날짜, 역순·동일 범위, 최댓값 날짜 overflow는 422. 유효한 범위의 끝 날짜 제외와 윤일은 유지.
- metrics/issues/series의 발전소 ID를 동일하게 검증. 형식이 유효한 미등록 ID는 빈 목록.
- 보고서 출처 필터: generic scope `all`, 공개/합성, 월 범위, 구형 payload의 manifest 호환, 원본 DB/파일 비변경, 다른 조직 비노출, 출처 파일 unavailable.
- 패키징: 프로젝트 버전 기반 파일명, 사용자 지정 출력, 해시 manifest, 기존 파일 보존, 강제 추적된 비밀·데이터 사전 차단, 이동한 파일의 이전 경로 제외.

## 실행 결과

| 검사 | 결과 |
|---|---|
| Windows 오프라인 | 80 passed, 2 skipped (외부 서비스 + symlink 권한) |
| WSL Ubuntu 오프라인 | 81 passed, 1 skipped (외부 서비스) |
| 실제 PostgreSQL·MinIO | 1 passed; 일별 복구 및 조회 API 포함 |
| 독립 합성 복구 데모 | 7개 활성 파티션, 커밋 실패 전후 결과 보존, 재처리 해시 일치 |
| 코드·문서 | Ruff, JS 문법, 저장소 내 링크·스크립트 경로, 원본 기획 8개 checksum 통과 |
| wheel·소스 ZIP | 0.3.1 빌드 성공, 정적 UI/보고서 템플릿/날짜 모듈 포함, ZIP 버전·목록/해시 검증 |
| Compose API | health/ready 200, 잘못된 날짜 범위·최댓값 날짜·ID 422, 실제 기존 공개/합성 보고서 출처 필터 성공 |
| Airflow 이미지 | 4개 DAG 및 공개/합성 템플릿 import 오류 0 |

로컬 검사에는 Starlette TestClient의 httpx 사용 중단 예정 경고 1건이 있습니다. 통과한 기능 검사와 구별하며, 지원 클라이언트 전환은 후속 의존성 갱신 시 검증합니다.

증거: `artifacts/pytest-v031-windows.xml`, `artifacts/api-v031.json`, `data/portfolio-v031-review/evidence.json`, `artifacts/dist-v031/`. 위 전체 검사 후 Windows에서 대소문자 변형 비밀파일 패키징 회귀 4개도 통과했습니다.

원본 기획 checksum 검사에서 기존 Git 사본의 `audit_plan.py` import 순서가 ZIP과 다름을 발견했습니다. 이전 사본은 `artifacts/archived-plan-before-restore-*.py`에 보존하고 ZIP의 정확한 바이트로 복원해 8개 모두 일치시켰습니다. 원본 ZIP과 manifest는 변경하지 않았습니다.

## 배포와 DAG 실행

새 worker/airflow 0.3.1 이미지를 Compose 및 kind에 배포했습니다. [이미지 ID](../image-versions.json)에 이전 버전과 함께 기록합니다. kind의 Helm revision은 7입니다.

- Compose 합성 5개 시나리오: `compose-synthetic-*-1792672294` 정상·실패재시도·백필·품질·보고서 성공. DB에서 `replay_validate_publish`의 try_number=2와 success를 확인했습니다.
- kind 공개 5개 시나리오: `k8s-public-*-1792672296` 계획·처리·백필·품질·보고서 성공. PS_001, 2024-04-03 포함~04 제외, brpvgen-v1.
- 각 환경의 4개 DAG는 검사 후 모두 pause 상태를 확인했습니다. 기존 데이터/PVC/실행 Pod/원본은 삭제하지 않았습니다.
- 실행 로그: `artifacts/airflow-compose-v031.log`, `artifacts/k8s-public-v031.log`.

## 원격 CI와 화면

[기능 커밋 658c814의 GitHub Actions](https://github.com/TaeyanG4/solarops-audit/actions/runs/39779616306)가 성공했습니다. Ubuntu/Windows 각각 **81 passed, 1 skipped**이며 두 환경 모두 의존성 설치·lint·문서/경로·JS 문법·정상 데모·복구 데모·wheel·소스 ZIP·lockfile·아티팩트 업로드까지 통과했습니다. 제외된 1개는 실제 서비스 통합 검사로, 로컬에서 별도 통과했습니다.

실제 8502 화면에서 v0.3.1 전체 현황, 기존 PS_001 공개 보고서, 합성 DEMO_01과 기존 `all` 보고서가 출처별로 표시됨을 확인했습니다. 선택한 발전소가 없는 자료 구분에서는 안내 후 사용 가능한 보고서를 선택하도록 유지합니다. 브라우저 콘솔 오류는 관찰되지 않았습니다. 최종 화면은 PS_001·2024년 4월 공개 보고서이며 증거는 `artifacts/report-v031.png`에 보존했습니다.

CI에는 현재 사용 중인 Actions의 Node 20→24 전환 안내가 남아 있습니다. 실행은 성공했으며, Actions 주 버전 갱신은 앱 의존성 갱신과 구분해 후속 검증합니다.

## 재현 명령

[기여 안내](../../CONTRIBUTING.md)의 검사와 독립 데모를 사용합니다. `scripts/validation/check_docs.py`는 외부 URL/문서 내부 heading anchor를 요청하지 않고 저장소 내 링크 대상·실행 경로·원본 기획 checksum을 검사합니다.

경로 개편으로 과거 검증 문서의 재현 명령도 새 경로에 맞췄습니다. 과거 측정값과 실행 환경은 유지했습니다. `.env`, 공개 원본, 실행 로그는 Git과 소스 ZIP에서 제외합니다.
