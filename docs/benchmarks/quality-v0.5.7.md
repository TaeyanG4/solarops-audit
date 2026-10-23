# v0.5.7 지표 계약 공유·읽기 전용 보고서 snapshot·배포 근거

2026-10-23 Asia/Seoul. 계산 `energy-interval-v2` 유지(저장 결과·논리 hash 불변). [릴리스·이미지](../releases/0.5.7.json) · [수행 기록](../worklog/2026-10-23-release-0.5.7.md) · [R6 평가 수용](../reviews/2026-10-23-artifact-r6.md).

## 변경

- 일별 지표 필수 필드(`REQUIRED_METRIC_FIELDS`, `analytics/metrics.py`)를 보고서와 overview API가 공유합니다. 필드가 없는 행은 보고서 생성 전 `METRIC_CONTRACT_MISMATCH`, overview는 503으로 응답하며 불명을 0으로 채우지 않습니다. 해당 필드는 최초 MVP부터 모든 생성기가 기록하며 생성기 출력 검사를 추가했습니다.
- overview의 보간 비중은 보고서와 같은 규칙으로, 관측 슬롯이 모두 보간 불명이면 `null`입니다.
- `report`는 snapshot을 읽기 전용 Catalog로 먼저 읽어 없는 SQLite 카탈로그를 만들지 않습니다(0.5.6 `analyze`와 같은 경계).
- `migrations/0001_catalog.sql`을 모델에서 재생성(13테이블·PostgreSQL 인덱스 2)하고 지원 경로는 `db-migrate`임을 명시, 정적 대조 검사를 추가했습니다.

## 실행한 검사

| 검사 | 결과 |
|---|---|
| 오프라인 `pytest -q` | 142통과·14제외(서비스 opt-in 13·호스트 symlink 1) |
| 실제 격리 PostgreSQL 16.10/MinIO 13개 서비스 검사 | 13통과 24.48초, 새 무작위 컨테이너는 중지·보존 |
| 새 검사 3개 역검증 | 이전 구현에서 실패, 새 구현에서 통과 |
| 참조 SQL | 임시 PostgreSQL 16.10에 `ON_ERROR_STOP=1` 적용, 13테이블·인덱스 2 |
| Ruff check/format, `release.py check`, 문서 링크 검사 | 통과, 선언 0.5.7 정렬 |
| GitHub Actions | 0.5.7 이전 보완 커밋들의 Windows/Ubuntu 검사 성공. 0.5.7 선언 커밋 이후 실행은 저장소 Actions에서 확인 |

## 배포

- `release.py build`로 깨끗한 구현 커밋 `4700c656b1a5`에서 `solarops-worker:0.5.7`(`sha256:3513846a…`)·`solarops-airflow:0.5.7`(`sha256:ab73605d…`)을 빌드했습니다.
- Compose: `up -d --no-deps dashboard`로 대시보드만 재생성, DB·MinIO 볼륨 유지. `/health` 0.5.7, `/ready` ready. 배포 전후 응답 비교: ONS 2026-10·보고서 목록은 동일, 2024-04 공개 overview는 **1개 필드만** 변경(4월 25일 일별 보간 비중 `0.0 → null`, 해당 날짜의 관측 슬롯이 모두 보간 불명). 월 요약 값은 동일합니다.
- kind: `scripts/ops/k8s-refresh.sh`로 이미지 로드·Helm 업그레이드·재시작. api-server/dag-processor/scheduler rollout 성공, 6개 서비스 Pod Ready, Airflow 이미지 0.5.7. KPO 작업 이미지는 Airflow 이미지의 `release.json`에서 `solarops-worker:0.5.7`. DAG 일시중지 상태 유지(ONS만 활성, 다른 6개 paused).

## 한계

- 새 scheduled KPO 작업은 이번에 실행하지 않았습니다(다음 ONS 일정 10-24 14:00 KST). 공개 전체 재처리·성능 재측정·화면 axe 재검사는 하지 않았습니다.
- Compose 프로젝트의 과거 시험용 컨테이너(orphan 경고 7개)는 보존 원칙에 따라 삭제하지 않았습니다.
- 독립 평가 반복은 사용자 요청으로 R6 이후 종료했으며 0.5.7 자체는 독립 평가하지 않았습니다.
