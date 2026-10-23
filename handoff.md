# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 앱 **v0.5.0** / 계산 `energy-interval-v2`. 구현 `853de23`와 [릴리스·이미지](docs/releases/0.5.0.json)를 연결했습니다. [GitHub](https://github.com/TaeyanG4/solarops-audit)는 비공개입니다.
- DATA-03/PERF-03 완료: [ONS 증분 계약](docs/ons-source-contract.md), 성공 cursor와 변경 날짜 원자 게시, 별도 CLI/API, 실제 정기 수집과 공개4일 Airflow 병렬 비교. [실행 근거·한계](docs/benchmarks/incremental-v0.5.0.md).
- ONS: Compose 10월 태양광 69,696행·21일, 같은 응답 재실행 변경 0개. kind 9~10월 167,424행·51일, 실제 scheduled KPO 성공. 두 환경의 10월 일별 hash 일치. 원문 시각/MWmed·검증/예측/미확정 보존, 기존 발전량에 합산하지 않습니다.
- 공개 4일 실제 KPO: 직렬 36.675초→동시 2개 19.339초(47.3% 단축), hash 동일·오류 0, worker RSS 최대 427.78MiB. 총 CPU 24.3% 증가. 별도 DB/버킷이며 단일 호스트·각 1회·4개의 일별 task 비교입니다.
- 검증: 로컬 136통과·14제외, 실제 PostgreSQL/MinIO 13통과, 양 실행 모드 7DAG 검사. 기존 공개 API 응답 3개는 전후 바이트 동일. [구현 CI39910321487](https://github.com/TaeyanG4/solarops-audit/actions/runs/39910321487)는 Ubuntu/Windows 각각 137통과·13제외입니다.
- 실행: Compose app-db/minio/dashboard와 kind 가동, 앱/Airflow/KPO 0.5.0. Compose Airflow 3개는 0.5.0으로 생성했지만 중지. kind **ONS만 활성**, 매일 14:00 KST, 다음 10-24 14시. 나머지 6DAG paused·진행/대기 0건. [수집 on/off](docs/runbooks/dags.md#ons-정기-수집-켜기끄기).
- [전체 현황](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public), [PS_001 보고서](http://127.0.0.1:8502/?view=reports&period=2024-04&source=public&plant=PS_001), [ONS API](http://127.0.0.1:8502/api/v1/sources/ons?period=2026-10). ONS 전용 대시보드는 없고 기존 화면은 BR-PVGen입니다.
- 공개 BR-PVGen 전체 51발전소/12,572일 v2는 Compose, kind 기존 공개는 PS_001 하루, 기본 native는 v1 보존본. 저장소 자동 동기화는 없습니다. [실사](docs/benchmarks/stack-authenticity-20261023.md).
- [독립 관리 8504](http://127.0.0.1:8504/)는 별도 호스트 Python, `scripts/ops/admin.ps1 stop`으로 종료. [운영](docs/runbooks/operator.md#시스템-관리-8504). 시험 DB/버킷/완료 Pod/원본은 삭제하지 않았습니다.
- 고객 계약·매출·현장 고장 정확도·외부 SLO·장시간 쓰기 부하는 미검증이며 공개 서비스 배포는 없습니다.

## 다음 재개 지점

- [plan](plan.md)에 합의된 미완료 기술 작업은 없습니다. BIZ-01은 사용자 요청으로 후순위이며 자동 전환하지 않습니다. 고객 운영/새 요구가 정해지면 범위·우선순위를 다시 점수화합니다.
- ONS는 이전/현재 월을 재확인하며 그보다 오래된 정정은 `ons-sync --period YYYY-MM`. 실패 시 월별 성공 cursor 유지, 충돌은 최신 상태에서 재시도. 원문 시간대를 추측해 UTC로 변환하지 않습니다.
- kind 중지 시 정기 수집도 멈춥니다. ONS만 멈추려면 DAG pause. 현재 실행 중인 Pod까지 강제 종료하는 명령은 아닙니다. 두 환경 자료는 독립입니다.
- 릴리스는 `scripts/release/release.py sync`→`uv lock`→`check`→구현커밋→`build`. 추가 테이블은 새 읽기 API 배포 전 `db-migrate`. 원본/과거 보고서 필드를 소급 변경하지 않습니다.
- 단발성·낮은 영향 수정은 기존 검사/화면 확인 우선. 연구 스킬과 discoveries 절차는 사용하지 않습니다. UI 변경은 [디자인](DESIGN.md)·[탐색계약](docs/design/workspace-navigation.md) 기준입니다.
- 원본·ZIP·`docs/plan/`·과거 증거 보존, 민감/파괴적 삭제는 사용자 허락 필요.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | ONS 실제 증분·정기 KPO·공개 DAG 동시 2개 비교, 0.5.0 배포·문서 갱신 | [수행·전달](docs/worklog/2026-10-23-incremental.md) |
| 10-23 | 입력/게시 4경계 수정·0.4.2 정렬·실제 KPO 재시도/추적·세 환경 7일 일치 | [구현·배포](docs/worklog/2026-10-23-integrity-delivery.md) |
| 10-23 | 독립 검토·경계 4개 재현·6개 후속 계획 | [수용 판단](docs/worklog/2026-10-23-independent-review.md) |
| 10-23 | 실제 수집/스케줄·환경별 아키텍처·README 정리 | [문서·상태](docs/worklog/2026-10-23-data-architecture.md) |
| 10-23 | 서비스 CI·보고서 비교·격리 복원·합성 10만 건 조회 부하 | [전달기록](docs/worklog/2026-10-23-technical-delivery.md) |
| 10-23 | 영업 후순위·MVP와 남은 기술 범위 구분 | [평가](docs/worklog/2026-10-23-technical-roadmap.md) |
| 10-23 | 문구·등록 월·보고서 기준·진단·발전소 조회 최적화 | [기록](docs/worklog/2026-10-23-usability.md) |
| 10-23 | 실행 이력 발전소 조회·URL 복원·상하위 링크 | [기록](docs/worklog/2026-10-23-run-navigation.md) |

100줄 이내·최근 요약 최대 8개. 이전 handoff/discoveries는 [원문 보관](docs/worklog/archive/README.md)이며 현재 지침이 아닙니다.
