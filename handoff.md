# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 최신 릴리스 **v0.5.7 / energy-interval-v2**, 선언 커밋 `4700c65`, Compose 대시보드·kind Airflow/KPO 배포 완료(22:00 KST 전후). [검사·배포](docs/benchmarks/quality-v0.5.7.md) · [릴리스·이미지](docs/releases/0.5.7.json) · [비공개 GitHub](https://github.com/TaeyanG4/solarops-audit).
- **독립 평가 반복 종료**(사용자 요청, 10-23): R5 Astra 96/Fable 94, R6 Fable 91(지적 5건 0.5.7 보완), R7은 시작 직후 중단해 점수 없음. [R6 판단](docs/reviews/2026-10-23-artifact-r6.md) · [종료·릴리스 기록](docs/worklog/2026-10-23-release-0.5.7.md).
- **22:10 KST 전부 중지(사용자 요청, 데이터 삭제 없음)**: kind 노드 `solarops-control-plane`, Compose dashboard → minio/app-db를 `stop`, 랜딩 8507(PID 50104)·관리 8504(`admin.ps1 stop`) 종료. 열린 포트 0, 실행 컨테이너 0, 컨테이너는 Exited로 보존, 볼륨 5개(app-db·app-data·minio·airflow-db·airflow-logs) 유지. kind 중지로 ONS 정기 수집도 멈췄습니다.
- 다시 켜기: 관리 `.\scripts\opsdmin.ps1 start` 후 [운영 절차](docs/runbooks/operator.md#8502가-열리지-않을-때) 또는 `docker compose --env-file .env -f infra/compose/compose.yaml start app-db minio dashboard` → `/ready`. kind는 `docker start solarops-control-plane` 후 Pod Ready 확인(ONS 수집 재개). 랜딩은 `python -m http.server 8507 --bind 127.0.0.1 --directory landing`.
- kind ONS 정기 수집 설정은 매일 14:00 KST(ONS만 활성, 다른 6개 DAG paused)이며 0.5.7 rollout 후 확인했습니다. 현재 kind가 중지되어 실행되지 않습니다. [일정 on/off](docs/runbooks/dags.md#ons-정기-수집-켜기끄기).
- 공개 BR-PVGen 전체 51발전소/12,572일 v2는 Compose, kind의 BR 자료는 PS_001 하루, native는 v1 보존본. ONS의 기존 검증 범위는Compose 69,696행/21일·kind 167,424행/51일. 환경별 저장소는 독립입니다. [수집 근거](docs/benchmarks/incremental-v0.5.0.md).
- 추정 kWh·검토 후보·누락/무효/보간을 구분합니다. ONS 원문 MWmed·시간 기준 미확정을 보존하고 기존 kWh에 합산하지 않습니다. 고객·매출·외부 SLO·장기 쓰기 부하는 미검증입니다.
- [독립 랜딩 v6](http://127.0.0.1:8507/) 완료. 히어로 카드를 실제 공개 집계 기반 데모 창(전체 현황/월간 보고서/원본 계보)으로 교체, 보고서 문서형·계보 4단계 흐름, CSS 재작성. 1440/768/375 렌더·axe위반0, 미검증 범위는 [작업 기록](docs/worklog/2026-10-23-landing.md#v6-히어로-실제-데모-창과-전체-다듬기)·[QA](landing/QA.md). [실행](landing/README.md). 별도 loopback 정적 서버이며 FastAPI는 이 작업에서 변경하지 않았습니다.

## 다음 재개 지점

1. AGENTS.md → 이 문서 → [plan.md](plan.md)를 읽습니다. 현재 실행 가능한 미완료 항목은 없고 BIZ-01은 사용자 요청으로 보류입니다.
2. 독립 평가는 종료했습니다. 다시 요청받으면 R6 방식(고정 커밋 사본·같은 prompt, Git 제외 `artifacts/artifact-review-r6-20261023/`)으로 실행하고, 평가자 사용량 문제는 AGENTS 규칙대로 일시중지합니다.
3. 사용자 결정이 필요한 저장소 점검 결과: 코드 라이선스 파일 없음, GitHub topics 미설정, 문서가 참조하지 않는 랜딩 이전 캡처 19장, Compose orphan 시험 컨테이너 7개(보존). [점검 기록](docs/worklog/2026-10-23-release-0.5.7.md#저장소-점검).
4. 릴리스는 `release.json` 변경 → `release.py sync` → `uv lock` → `check` → 구현 커밋 → `build` → Compose `up -d --no-deps dashboard` → WSL `bash scripts/ops/k8s-refresh.sh`. 계산 버전이 바뀌면 과거 결과를 소급 변경하지 않습니다.
5. 현재 모든 로컬 서비스가 중지 상태입니다(위 다시 켜기 참고). kind를 멈추면 ONS 정기 수집도 멈춥니다. ONS만 멈추려면 DAG pause. 원본/ZIP/볼륨/과거 평가 보존, 민감한 삭제는 사용자 허락이 필요합니다.
6. 단발성·낮은 영향 수정은 기존 검사/화면 확인 우선. UI 변경은 [디자인](DESIGN.md)·[탐색계약](docs/design/workspace-navigation.md), 랜딩은 [landing/DESIGN.md](landing/DESIGN.md) 기준입니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 평가 반복 종료·0.5.7 빌드/Compose·kind 배포·저장소 점검·README 최신화 | [종료·릴리스·점검](docs/worklog/2026-10-23-release-0.5.7.md) |
| 10-23 | 랜딩 v6 히어로 데모 창·보고서/계보 재구성, v5 HTML/SVG 제품 화면·세너비 검수 | [랜딩 구현·검수](docs/worklog/2026-10-23-landing.md) |
| 10-23 | R5 Astra 96 / Fable 94·원문 보존·hash 설명 정정·다음 세션 인계 | [인계·검증](docs/worklog/2026-10-23-handoff-r5.md), [R4 구현](docs/worklog/2026-10-23-quality-r5.md) |
| 10-23 | Fable·Astra 면접 평가·합성 경계 3개 재현·후속 21/19/16점 등록 | [평가·재현·전달](docs/worklog/2026-10-23-interview.md) |
| 10-23 | PORT-01~04완료·ONS상태UI·0.5.1배포·격리재현·제출자료·최신CI | [최종 수행](docs/worklog/2026-10-23-portfolio-finish.md) |
| 10-23 | ONS 실제 증분·정기 KPO·공개 DAG 동시 2개 비교, 0.5.0 배포·문서 갱신 | [수행·전달](docs/worklog/2026-10-23-incremental.md) |
| 10-23 | 입력/게시 4경계 수정·0.4.2 정렬·실제 KPO 재시도/추적·세 환경 7일 일치 | [구현·배포](docs/worklog/2026-10-23-integrity-delivery.md) |
| 10-23 | 독립 검토·경계 4개 재현·6개 후속 계획 | [수용 판단](docs/worklog/2026-10-23-independent-review.md) |

100줄 이내·최근 요약 최대 8개. 이전 handoff/discoveries는 [원문 보관](docs/worklog/archive/README.md)이며 현재 지침이 아닙니다.
