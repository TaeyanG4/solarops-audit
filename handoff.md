# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 앱 v0.4.1 / 계산 `energy-interval-v2`. 공개·합성 자료의 엔지니어링 MVP와 로컬 시연을 구현·검증했습니다.
- 전체 현황 리디자인 완료. [공개 2024년 4월 화면](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public), [GitHub](https://github.com/TaeyanG4/solarops-audit) 비공개 유지.
- UI 기능 `afd6169`의 [CI](https://github.com/TaeyanG4/solarops-audit/actions/runs/39812883684): Windows/Ubuntu 각각 113통과·5제외. 로컬 Windows 112통과·6제외와 구분합니다.
- README·출처·스킬·이미지와 기록 구조 개선 완료. `dbbe744` GitHub 반영, CI 양 OS 각각 113통과·5제외, 문서·복원·패키징 성공. [상세 근거](docs/worklog/2026-10-23.md).
- 10-23 접속 장애: 중지된 Compose app-db·minio·dashboard를 다시 시작해 준비 상태·PS_001 보고서 조회를 확인했습니다. Airflow는 중지, kind 컨테이너는 작업 시작 전부터 실행 중이었습니다. [재시작 안내](docs/runbooks/operator.md#8502가-열리지-않을-때).
- 실제 고객 계약·매출·현장 고장 정확도·외부 운영 SLO는 검증하지 않았습니다.

## 다음 재개 지점

- [plan](plan.md)의 실행 가능한 최고 점수부터 처리합니다. 완료 항목은 제거합니다.
- 고객 검증 BIZ-01(16점)은 승인된 대상·연락 방식·자료가 없어 대기 중입니다. 기술 시연을 매출 실적으로 바꾸어 기록하지 않습니다.
- 새 UI 작업은 [디자인 시스템](docs/design/overview-system.md)과 [기존 검증](docs/benchmarks/overview-redesign-20261023.md)을 기준으로 범위와 점수를 등록합니다.
- 원본 데이터·ZIP·`docs/plan/`은 보존합니다. 민감하거나 파괴적인 삭제는 사용자 허락이 필요합니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 중지된 서비스 3개 복구·보고서 확인, 2배 픽셀 밀도 캡처와 본문 폭 조정·원본 확대 링크 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | README 보강, 직접 출처·스킬 사용 목적, 최신 캡처, 짧은 인계와 일자별 기록으로 통일 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | 전체 현황 정보 위계·차트·품질·반응형 개선, 세 너비·키보드·오류·API 보존 검증 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | 보존 raw·동시 버전·보고서 역순 완료·조회 부작용·파일 무결성 수정 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-22 | 계산 v2, 공개 전체 비교, 읽기 전용 진단, 합성 로컬·서비스 복원 검증 | [작업 기록](docs/worklog/2026-10-22.md) |
| 10-22 | 월별 조회 53회→1회, 스크립트·패키징·운영 문서 정리 | [작업 기록](docs/worklog/2026-10-22.md) |
| 10-22 | 공개 51개 발전소 처리, 공통 CLI와 Compose·Airflow·KPO 실행 검증 | [작업 기록](docs/worklog/2026-10-22.md) |
| 10-22 | 파일럿 범위·원가 가정·측정 양식 정리, 실제 고객 근거는 대기 | [작업 기록](docs/worklog/2026-10-22.md) |

이 파일은 100줄 이내·최근 요약 최대 8개로 유지합니다. 이전 handoff/discoveries는 [원문 보관본](docs/worklog/archive/README.md)에 있으며 현재 작업 지침이 아닙니다. research-orchestrator 스킬은 사용하지 않습니다.
