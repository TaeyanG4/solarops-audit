# v0.4.0 계산 경계·진단·복원 검증

기준: 2026-10-22. [현재 상태](../IMPLEMENTATION_STATUS.md) · [계산 버전 결정](../adr/0007-calculation-v2.md) · [발견 기록](../../discoveries.md)

## 계산 v2

무효 전력을 실제 0과 구분하고, UTC가 아닌 현지 날짜의 원본 경계를 수정했다. 품질·후보·시계열을 논리 해시에 포함한다. 에너지 산식은 유지했다. 새 경계 회귀 8개 중 수정 전 4개가 실패했고(3개 결함 재현+v2 요건), 수정 후 관련 파이프라인 18개가 통과했다. DST 23/25시간 전체 누락일의 기대 슬롯도 확인했다.

실제 PostgreSQL·MinIO에 공개 51개 발전소, 인버터 14,400,480행, 일별 12,572개를 v2로 적재했다. 처리·보고서 생성은 859.533초였다. v1의 활성 ID·해시·지표가 그대로인지 저장한 기준과 대조했다. 모든 일별 지표는 calculation_version을 제외하고 같고 모든 원본 SHA도 같다. 서로 다른 계산 버전의 논리 해시는 달라야 한다.

결정적 표본 31개 시계열의 2,976개 슬롯 중 190개가 0→null로 수정됐다. 그 외 필드는 모두 같고 수정 슬롯은 INSUFFICIENT_DATA였다. **전체 일별 지표 비교와 표본 시계열 비교는 검증 범위가 다르다.** 이번에는 서비스 전체를 처리했으며 기존 네이티브 전체 카탈로그를 v2로 다시 처리하지 않았다. 과거 v1 native/서비스 해시 일치는 별도 초기 검증이다.

증거: `artifacts/public-v1-before-v040.json`, `artifacts/full-dataset-v040-services.jsonl`, `artifacts/full-dataset-v040-console.log`, `artifacts/public-v1-v2-comparison.json`. 새 v2 보고서를 만들었고 기존 보고서 파일은 유지했다.

## 진단과 복원

- `inspect-runs`: SQLite의 부재·read-only, 조직 격리, active 자식, 경과시간·시각 누락·미래 시각, 페이지, DB 비변경을 7개 테스트로 확인했다. 실제 PostgreSQL에서 진행 중 batch 1개를 정상 경과시간으로 조회했다.
- 합성 복원: 7개 일별 파티션, DB 포함 31파일의 SHA 확인, SQLite integrity 정상, 손상 사본 거부, 새 경로의 현황·시계열·과거 보고서 API 성공, 복원 raw 재처리 해시 일치와 새 보고서 생성. 원본/백업 보존.
- 첫 복원 시도는 검증 스크립트의 보고서 URL 오타로 중단됐다. 올바른 `/reports/...`로 고친 뒤 **새 폴더**에서 성공했다. 실패 증거 `artifacts/restore-v040.log`도 보존했다.

복원 범위는 쓰기가 끝난 전용 합성 SQLite/로컬 파일이며 PostgreSQL·MinIO, 동시 생산자, 다른 호스트의 재해복구는 미검증이다. [복원 계약과 다음 조건](../runbooks/backup-restore.md). 성공 증거: `data/restore-v040-verified/evidence.json`, `data/restore-v040-verified/backup-manifest.json`.

## 실행 결과

| 검사 | 결과 |
|---|---|
| Windows 전체 오프라인 | 95 passed, 2 skipped (서비스·symlink 권한) |
| WSL Ubuntu 전체 오프라인 | 96 passed, 1 skipped (서비스) |
| 실제 PostgreSQL·MinIO | 1 passed |
| 독립 합성 정상·실패·재처리 | 7개 활성 파티션 유지, 반복 해시 일치 |
| Airflow 0.4.0 이미지 | 4개 DAG·공개/합성 템플릿, import 오류 0 |
| Compose 0.4.0 API | health/ready 200, 공개 4월 5개 발전소·140개 일별 파티션, v2 보고서 2개 |

Ruff·문서 링크·스크립트 참조·원본 기획 8개 checksum 검사 통과. TestClient의 httpx 사용 중단 예정 경고는 기존과 같다. 소스 ZIP에 원본 데이터·비밀값·실행 로그는 포함하지 않는다.

## 배포 후 확인

Compose/kind 0.4.0 이미지 적용 후 실제 DAG 실행을 확인했다. [이미지 ID](../image-versions.json)는 이전 버전과 함께 보존한다.

- Compose `compose-synthetic-*-1792678191`: 정상·실패재시도·백필·품질·보고서 5개 성공. DB의 replay_validate_publish try_number=2/success 확인.
- kind `k8s-public-*-1792678310`: 계획·처리·백필·품질·보고서 5개 성공. PS_001/2024-04-03 포함~04 제외/brpvgen-v1. kind는 이 날짜 범위만 v2 처리했으며 Compose의 전체 카탈로그와 별도다.
- 검사 후 각 환경의 4개 DAG는 모두 pause 상태. 이전 이미지·DB·객체·PVC는 보존했다.
- 8502 브라우저: PS_001/2024년 4월/30개 일별 파티션, energy-interval-v2 보고서와 앱 v0.4.0 확인. 콘솔 오류 관찰 없음. `artifacts/report-v040.png`.
- wheel 0.4.0에 UI 정적 파일·보고서 템플릿·진단 모듈 포함 확인.

로그: `artifacts/airflow-compose-v040.log`, `artifacts/k8s-public-v040-execution.log`, `artifacts/deploy-compose-v040.log`, `artifacts/deploy-kind-v040.log`. 첫 WSL 호출은 PATH 인용 오류로 실행 전에 종료됐고, 제한된 PATH를 env 인수로 전달해 정상 실행했다.

원격 CI는 기능 커밋 push 후 확인하여 아래에 결과를 기록한다.
