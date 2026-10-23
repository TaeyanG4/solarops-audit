# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 앱 **v0.4.2** / 계산 `energy-interval-v2`. 구현 `2f42cbe`와 [릴리스·이미지 증거](docs/releases/0.4.2.json)를 연결했습니다. [GitHub](https://github.com/TaeyanG4/solarops-audit)는 비공개입니다.
- [DATA-02/PUB-01/OPS-08/OPS-09 완료](docs/worklog/2026-10-23-integrity-delivery.md): canonical 인버터 ID, 완료 CSV만 노출, metadata+조건부 active 원자 게시, 명시적 과거 복원, 단일 릴리스와 Airflow/Pod/재시도 추적.
- [실행 근거](docs/benchmarks/integrity-v0.4.2.md): 격리 PostgreSQL/MinIO12통과, Native/Compose/실제KPO 합성7일 해시·보고서18필드 일치(추정832.424kWh), 실제1차 실패/2차 성공과 진단 연결. 공개 overview·PS_001 series·기존 보고서 HTML 전후 바이트 동일.
- [구현 CI39906673530](https://github.com/TaeyanG4/solarops-audit/actions/runs/39906673530): Ubuntu/Windows 각각134통과·12제외, 릴리스 선언·합성 데모·복원·패키징 성공. 미실행 인프라를 통과로 집계하지 않습니다.
- 실행 상태: Compose app-db/minio/dashboard와 kind 실행. dashboard·kind Airflow/KPO0.4.2 반영. Compose Airflow 새 컨테이너는 중지 상태. 검증 후 DAG4개 paused, running/queued0건. 시험 서비스 컨테이너도 중지·보존했습니다.
- [전체 현황](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public), [PS_001 보고서](http://127.0.0.1:8502/?view=reports&period=2024-04&source=public&plant=PS_001). 분석/감사/관리7개 목적지,16/14px 글씨·공통 선택창·favicon·iframe 없는 보고서입니다.
- [실제 자료/기술 실사](docs/benchmarks/stack-authenticity-20261023.md): 원본4개·CSV102개 계보/해시, 대표 계산·DB/API/보고서/kind 대조. 공개전체51발전소/12,572일 v2는 Compose, kind공개는 PS_001하루, 기본native는 v1보존본입니다. 저장소는 자동 동기화하지 않습니다.
- [이전 성능·복원](docs/benchmarks/technical-20261023.md): 합성10만 건 동시4 깊은 페이지 p95 6409→679ms, 전후1080요청 오류0. 별도 인스턴스 복원은 같은 물리 호스트 시험입니다.
- [독립 관리8504](http://127.0.0.1:8504/)는 별도 호스트 Python이며 `scripts/ops/admin.ps1 stop`으로 종료합니다. [on/off 운영 안내](docs/runbooks/operator.md#시스템-관리-8504).
- 고객 계약·매출·현장 고장 정확도·외부 SLO·장시간 쓰기 부하는 검증하지 않았습니다. 공개 서비스 배포는 하지 않았습니다.

## 다음 재개 지점

- [plan](plan.md)은 미완료만 유지합니다. 다음은 DATA-03(19점) 실제 갱신 원천의 계약/증분 수집, PERF-03(14점) 목표 기반 제한 병렬 측정입니다. BIZ-01(16점)은 사용자 요청으로 후순위입니다.
- ONS 시간별 발전의 최근 갱신 metadata/16KB 표본을 확인했습니다. 일부 소규모 그룹은 예측, 시각은 offset 없음입니다. 단위·시간대·예측 분리·라이선스 버전·ID 계약을 확정한 뒤 adapter/cursor를 구현합니다. 기존 BR-PVGen public로 단순 변환하지 않습니다.
- 신규 정기 수집은 아직 없습니다. 고정 BR-PVGen 다운로드와 역사구간 DAG를 구분합니다. [수집 안내](docs/guides/data-ingestion.md), [아키텍처](docs/architecture/system.md). PERF-03 처리시간/자원 목표도 미확정이며 spill만 준비했습니다.
- 릴리스 변경은 `scripts/release/release.py sync`→`uv lock`→`check`→구현 커밋→`build`. Git revision 없는 일반빌드는 `unrecorded`로 표시됩니다. 과거 Pod/보고서의 누락 필드는 소급 변경하지 않습니다.
- 동시 게시 충돌은 현재 active를 확인한 뒤 재시도합니다. 과거 성공 버전을 되돌리려면 `ingest/backfill --restore`; 복원도 동시성 검사 유지. 원자성은 날짜별이며 앞서 성공한 날짜는 유지됩니다.
- 단발성·낮은 영향 수정은 기존 검사/화면 확인을 우선합니다. 이번 추가 검사는 데이터 무결성·게시·추적 계약에 한정했습니다. 연구 스킬과 discoveries 유지 절차는 사용하지 않습니다.
- UI 변경은 [현재 디자인](DESIGN.md), [방향 계약](docs/design/workspace-navigation.md), [목록 동작](docs/benchmarks/select-anchor-20261023.md)을 기준으로 합니다.
- 원본 데이터·ZIP·`docs/plan/`·과거 증거를 보존합니다. 민감하거나 파괴적인 삭제는 사용자 허락이 필요합니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 입력/게시 경계4개 수정, 릴리스0.4.2 정렬, 실제KPO 재시도/추적·세환경7일 일치·양OS CI134통과 | [구현·배포 기록](docs/worklog/2026-10-23-integrity-delivery.md) |
| 10-23 | 독립 검토 완료, 경계4개 합성 대조·재현, 입력/게시/릴리스 우선의 6개 후속 계획 | [수용 판단·근거](docs/worklog/2026-10-23-independent-review.md) |
| 10-23 | 실제 수집/스케줄·추가 데이터 범위 확인, 환경별 아키텍처·README·운영 문서 최신화 | [문서·실행 상태 기록](docs/worklog/2026-10-23-data-architecture.md) |
| 10-23 | 선택형 서비스 CI5통과·보고서 비교·독립 인스턴스 복원·합성10만 건 부하 및 정렬 인덱스, 관련21검사·실제3너비 | [전달 기록](docs/worklog/2026-10-23-technical-delivery.md) |
| 10-23 | 영업 후순위 반영, MVP 완료와 남은 기술 범위 구분; 기존 서비스 검사 CI·보고서 변경 비교·격리 복원·동시 부하 후보 점수화 | [평가 기록](docs/worklog/2026-10-23-technical-roadmap.md) |
| 10-23 | 문구·실제 등록 월·보고서 기준 시점·읽기 전용 진단, 실측 후 인덱스1개로 발전소 조회393→15ms | [작업 기록](docs/worklog/2026-10-23-usability.md) |
| 10-23 | 개선 후보 점수화, 실행 이력 발전소 조회·URL/브라우저 이력 복원·상하위 링크, 기존5테스트·3너비 확인 | [작업 기록](docs/worklog/2026-10-23-run-navigation.md) |
| 10-23 | 스크롤 자동 닫힘을 사용자 요구에 맞춰 열림 유지·버튼 정렬로 교체, 269명령·3너비·axe6회 위반0 | [작업 기록](docs/worklog/2026-10-23-select-anchor.md) |

이 파일은 100줄 이내·최근 요약 최대 8개로 유지합니다. 이전 handoff/discoveries는 [원문 보관본](docs/worklog/archive/README.md)에 있으며 현재 작업 지침이 아닙니다. research-orchestrator 스킬은 사용하지 않습니다.
