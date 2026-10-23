# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- [독립 기술 검토](docs/worklog/2026-10-23-independent-review.md): 별도 세션 검토와 본 세션의 합성 재현으로 ID 혼용 분모·중단 추출·실패 metadata·일별 역순 게시를 확인했습니다. [후속 구현](docs/worklog/2026-10-23-integrity-delivery.md)에서 DATA-02/PUB-01 수정과 로컬133·격리 서비스11검사를 완료했습니다. OPS-08 이미지 정렬/배포·OPS-09 실환경 추적 검증을 진행합니다.
- [수집·아키텍처 최신화](docs/worklog/2026-10-23-data-architecture.md): 고정 BR-PVGen 수동 다운로드와 역사 구간 DAG를 구분했습니다. 13:11 KST Compose Airflow 중지·kind DAG4개 paused·진행/대기0건. [수집·확장 안내](docs/guides/data-ingestion.md), [아키텍처](docs/architecture/system.md), README를 실제 구현/배포 범위에 맞췄습니다.
- [최신 기술 후속](docs/worklog/2026-10-23-technical-delivery.md): 선택형 실제 서비스 CI·보고서 게시 근거 비교·별도 인스턴스 복원·동시 부하 완료. 합성10만 건 동시4 깊은 페이지 p95 6409→679ms, 전후1080요청 오류0. dashboard `0.4.1-technical-final-20261023`, 이전 보고서·공개 overview·인덱스 전후 카탈로그 행 보존.

- 앱 v0.4.1 / 계산 `energy-interval-v2`. 공개·합성 자료의 엔지니어링 MVP와 로컬 시연을 구현·검증했습니다.
- [실제 기술·자료 실사](docs/benchmarks/stack-authenticity-20261023.md): 원본4개·CSV102개·공개 계보103개 해시 대조, 대표 독립 계산과 DB/API/보고서/kind 일치. 실제 Airflow44개 실행·KPO80개 태스크 이력 확인. 합성 DEMO_01·장애 주입은 시험으로 분리했습니다.
- 현재 UI는 **분석/감사/관리의 7개 사이드바 목적지**, 본문16px·보조14px, 공통 월/목록 선택창·favicon입니다. [전체 현황](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public), [GitHub](https://github.com/TaeyanG4/solarops-audit) 비공개 유지.
- [실행 이력 OPS-06](docs/worklog/2026-10-23-run-navigation.md): 발전소 조회·주소로 필터/페이지/상세 복원·상하위 이동. 기존5테스트·3너비·브라우저74명령·모바일axe 위반0, 영구 검사 추가0. 이미지 `0.4.1-run-navigation-20261023`을 dashboard에 반영했습니다.
- [현재 목록 UI-05](docs/benchmarks/select-anchor-20261023.md): 스크롤 중 닫힘을 사용자 피드백으로 교체, 열린 채 버튼에 붙여 이동. 당시3너비·269명령·axe6회 위반0, API 동일. 관리 직접 진입·세 탭·실제 null 안내는 [UI-04](docs/benchmarks/interactions-20261023.md)에서 유지.
- [PS_001 보고서](http://127.0.0.1:8502/?view=reports&period=2024-04&source=public&plant=PS_001)는 iframe 없는 통합 본문입니다. 독립 인쇄 HTML도 새 양식으로 발행했고 이전UUID·원본 자료를 보존했습니다.
- 이전 워크스페이스 검사: Python126통과·6제외, Agent Browser107+195명령, axe3+23회 위반0, API 동일. 별도 최종 UI검수는 `ship`. [범위·한계·근거](docs/benchmarks/workspace-20261023.md).
- 최신 기능 `4d8b28c`의 [선택형 CI](https://github.com/TaeyanG4/solarops-audit/actions/runs/39897515593)는 PostgreSQL/MinIO5통과, 로컬 관련21통과·3너비 확인입니다. 이전 `d225e19`의 양OS127통과·5제외는 [당시 증거](docs/worklog/2026-10-23-usability.md)이며 이번 전체 회귀 결과가 아닙니다.
- 실행 상태: Compose app-db/minio/dashboard와 SolarOps kind 실행, Compose Airflow중지. kind서비스6Pod Ready이나 DAG4개 paused. kind v2는 공개하루, 전체공개 v2는 Compose에 있습니다. [독립 관리8504](http://127.0.0.1:8504/)는 별도 호스트 Python이며 `scripts/ops/admin.ps1 stop`으로 종료합니다. [on/off 안내](docs/runbooks/operator.md#시스템-관리-8504).
- 실제 전체중지→기본3서비스시작→kind시작을 검증했습니다. 다른 Docker프로젝트는 유지했고, kind노드 실행을 모든Pod준비 완료로 해석하지 않습니다.
- 실제 고객 계약·매출·현장 고장 정확도·외부 운영 SLO는 검증하지 않았습니다.

## 다음 재개 지점

- [검증 범위 조정](docs/worklog/2026-10-23.md#검증-범위-조정): 단발성·낮은 영향 수정은 기존 검사와 해당 화면 확인을 우선합니다. 회귀 검사·전용 스크립트는 재발 위험이나 영향이 유지 비용을 정당화할 때만 추가합니다. AGENTS.md에 반영했습니다.
- [plan](plan.md)의 실행 가능한 최고 점수부터 처리합니다. 완료 항목은 제거합니다.
- 다음은 DATA-02(22점) 입력 경계, PUB-01(21점) 게시 계약, OPS-08(20점) 릴리스 정렬입니다. DATA-03(19점)은 원천 선정 후, OPS-09(17점)는 게시/배포 정렬 후, PERF-03(14점)은 성능 목표 후입니다. 이전 TECH-01~04 완료와 새로 발견한 경계 결함을 구분합니다.
- 새 원천 정기 수집은 미구현입니다. 다른 데이터 추가 시 source_kind만 바꾸지 말고 출처/DOI·라이선스·adapter·증분 상태부터 확장해야 합니다. 현재 V.1 전체는 Compose에 처리되어 있으며 native/kind와 자동 동기화하지 않습니다. 이번 문서 작업에서는 서비스·자료·스케줄을 변경하지 않았습니다.
- 시험 컨테이너·8505 합성 미리보기·Agent Browser는 중지했고 GitHub 일회성 실행기 등록0개를 확인했습니다. 자료/컨테이너/백업은 보존합니다. 이번에는 dashboard만 재배포했고 기존 Airflow/kind 작업 이미지는 유지했습니다. 그 경로의 구버전 보고서는 선택 범위가 없어 비교 불가로 표시될 수 있습니다.
- 기본 native DB는 v1 보존본이며 MinIO 재현빌드는 실사 범위 밖입니다.
- 고객 검증 BIZ-01(16점)은 사용자 요청으로 후순위입니다. 승인된 대상·연락 방식·자료도 없으며 기술 시연을 매출 실적으로 바꾸어 기록하지 않습니다.
- 새 UI작업은 [현재 디자인 시스템](DESIGN.md), [방향 계약](docs/design/workspace-navigation.md), [최신 목록 검증](docs/benchmarks/select-anchor-20261023.md)을 기준으로 합니다. 수평 Energy Desk는 중간안입니다.
- 원본 데이터·ZIP·`docs/plan/`은 보존합니다. 민감하거나 파괴적인 삭제는 사용자 허락이 필요합니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 독립 검토 완료, 경계4개 합성 대조·재현, 입력/게시/릴리스 우선의 6개 후속 계획 | [수용 판단·근거](docs/worklog/2026-10-23-independent-review.md) |
| 10-23 | 실제 수집/스케줄·추가 데이터 범위 확인, 환경별 아키텍처·README·운영 문서 최신화 | [문서·실행 상태 기록](docs/worklog/2026-10-23-data-architecture.md) |
| 10-23 | 선택형 서비스 CI5통과·보고서 비교·독립 인스턴스 복원·합성10만 건 부하 및 정렬 인덱스, 관련21검사·실제3너비 | [전달 기록](docs/worklog/2026-10-23-technical-delivery.md) |
| 10-23 | 영업 후순위 반영, MVP 완료와 남은 기술 범위 구분; 기존 서비스 검사 CI·보고서 변경 비교·격리 복원·동시 부하 후보 점수화 | [평가 기록](docs/worklog/2026-10-23-technical-roadmap.md) |
| 10-23 | 문구·실제 등록 월·보고서 기준 시점·읽기 전용 진단, 실측 후 인덱스1개로 발전소 조회393→15ms | [작업 기록](docs/worklog/2026-10-23-usability.md) |
| 10-23 | 개선 후보 점수화, 실행 이력 발전소 조회·URL/브라우저 이력 복원·상하위 링크, 기존5테스트·3너비 확인 | [작업 기록](docs/worklog/2026-10-23-run-navigation.md) |
| 10-23 | 스크롤 자동 닫힘을 사용자 요구에 맞춰 열림 유지·버튼 정렬로 교체, 269명령·3너비·axe6회 위반0 | [작업 기록](docs/worklog/2026-10-23-select-anchor.md) |
| 10-23 | 선택창 스크롤 이탈·관리 직접 탐색/탭 수정, 원본 빈값 대조·차트 안내, 3너비·303명령·31테스트 | [작업 기록](docs/worklog/2026-10-23-interactions.md) |

이 파일은 100줄 이내·최근 요약 최대 8개로 유지합니다. 이전 handoff/discoveries는 [원문 보관본](docs/worklog/archive/README.md)에 있으며 현재 작업 지침이 아닙니다. research-orchestrator 스킬은 사용하지 않습니다.
