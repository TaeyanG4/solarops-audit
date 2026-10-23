# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 앱 v0.4.1 / 계산 `energy-interval-v2`. 공개·합성 자료의 엔지니어링 MVP와 로컬 시연을 구현·검증했습니다.
- [실제 기술·자료 실사](docs/benchmarks/stack-authenticity-20261023.md): 원본4개·CSV102개·공개 계보103개 해시 대조, 대표 독립 계산과 DB/API/보고서/kind 일치. 실제 Airflow44개 실행·KPO80개 태스크 이력 확인. 합성 DEMO_01·장애 주입은 시험으로 분리했습니다.
- 현재 UI는 **분석/감사/관리의 7개 사이드바 목적지**, 본문16px·보조14px, 공통 월/목록 선택창·favicon입니다. [전체 현황](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public), [GitHub](https://github.com/TaeyanG4/solarops-audit) 비공개 유지.
- [후속 UI-04](docs/benchmarks/interactions-20261023.md): 선택창 바깥 스크롤 닫힘·내부 스크롤 유지, 시스템관리 직접 진입·세 탭, 실제 차트 null 구간 설명. 원본 전력390개 빈 필드 확인. Python31통과·브라우저303명령·axe18회 위반0, API 동일. 이미지 `0.4.1-ui04-20261023` 배포.
- [PS_001 보고서](http://127.0.0.1:8502/?view=reports&period=2024-04&source=public&plant=PS_001)는 iframe 없는 통합 본문입니다. 독립 인쇄 HTML도 새 양식으로 발행했고 이전UUID·원본 자료를 보존했습니다.
- 로컬 검사: Python126통과·6제외, Agent Browser107+195명령, axe3+23회 위반0, API 동일. 별도 최종 UI검수는 `ship`. [범위·한계·근거](docs/benchmarks/workspace-20261023.md).
- 기능 커밋 `0618ce1` 비공개 GitHub 반영. [CI](https://github.com/TaeyanG4/solarops-audit/actions/runs/39841897047)는 Windows/Ubuntu 각각127통과·5제외, 합성 데모·복원·wheel·소스 패키징 모두 성공했습니다. DESIGN/sidecar·README·캡처·스킬 목적도 갱신했습니다.
- 실행 상태: Compose app-db/minio/dashboard와 SolarOps kind 실행, Compose Airflow중지. kind서비스6Pod Ready이나 DAG4개 paused. kind v2는 공개하루, 전체공개 v2는 Compose에 있습니다. [독립 관리8504](http://127.0.0.1:8504/)는 별도 호스트 Python이며 `scripts/ops/admin.ps1 stop`으로 종료합니다. [on/off 안내](docs/runbooks/operator.md#시스템-관리-8504).
- 실제 전체중지→기본3서비스시작→kind시작을 검증했습니다. 다른 Docker프로젝트는 유지했고, kind노드 실행을 모든Pod준비 완료로 해석하지 않습니다.
- 실제 고객 계약·매출·현장 고장 정확도·외부 운영 SLO는 검증하지 않았습니다.

## 다음 재개 지점

- [plan](plan.md)의 실행 가능한 최고 점수부터 처리합니다. 완료 항목은 제거합니다.
- 요청된 UI·보고서·관리 구현과 기술/자료 실사를 완료했습니다. 추가 사용자 피드백 또는 고객 검증 입력이 다음 재개 조건입니다. 기본 native DB는 v1 보존본이며 MinIO 재현빌드는 실사 범위 밖입니다.
- 고객 검증 BIZ-01(16점)은 승인된 대상·연락 방식·자료가 없어 대기 중입니다. 기술 시연을 매출 실적으로 바꾸어 기록하지 않습니다.
- 새 UI작업은 [현재 디자인 시스템](DESIGN.md), [방향 계약](docs/design/workspace-navigation.md), [최신 상호작용 검증](docs/benchmarks/interactions-20261023.md)을 기준으로 합니다. 수평 Energy Desk는 중간안입니다.
- 원본 데이터·ZIP·`docs/plan/`은 보존합니다. 민감하거나 파괴적인 삭제는 사용자 허락이 필요합니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 선택창 스크롤 이탈·관리 직접 탐색/탭 수정, 원본 빈값 대조·차트 안내, 3너비·303명령·31테스트 | [작업 기록](docs/worklog/2026-10-23-interactions.md) |
| 10-23 | 실행 스택·원본 해시·독립 계산·공개/합성 구분·실제 KPO 이력 대조, 검증 범위 명시 | [작업 기록](docs/worklog/2026-10-23-authenticity.md) |
| 10-23 | 사이드바7개 목적지·별도관리8504·실제중지/복구, 선택창·폰트·통합보고서·새인쇄물·최종검수 | [작업 기록](docs/worklog/2026-10-23-workspace.md) |
| 10-23 | 기존과 비슷하다는 피드백 후 Energy Desk로 새로 작성, 네 스킬 적용·3너비·결측/0·검수·원본 출처 개선 | [작업 기록](docs/worklog/2026-10-23-overview-v2.md) |
| 10-23 | 중지된 서비스 3개 복구·보고서 확인, 2배 픽셀 밀도 캡처와 본문 폭 조정·원본 확대 링크 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | README 보강, 직접 출처·스킬 사용 목적, 최신 캡처, 짧은 인계와 일자별 기록으로 통일 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | 전체 현황 정보 위계·차트·품질·반응형 개선, 세 너비·키보드·오류·API 보존 검증 | [작업 기록](docs/worklog/2026-10-23.md) |
| 10-23 | 보존 raw·동시 버전·보고서 역순 완료·조회 부작용·파일 무결성 수정 | [작업 기록](docs/worklog/2026-10-23.md) |

이 파일은 100줄 이내·최근 요약 최대 8개로 유지합니다. 이전 handoff/discoveries는 [원문 보관본](docs/worklog/archive/README.md)에 있으며 현재 작업 지침이 아닙니다. research-orchestrator 스킬은 사용하지 않습니다.
