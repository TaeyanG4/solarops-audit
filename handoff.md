# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-23 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- 최신 구현 **v0.5.6 / energy-interval-v2**, 구현 커밋 `4b9959e`, R5 평가 고정 커밋 `faa6f3b`. [릴리스·이미지](docs/releases/0.5.6.json) · [검증](docs/benchmarks/quality-v0.5.6.md) · [비공개 GitHub](https://github.com/TaeyanG4/solarops-audit).
- **R5 Astra 96 / Fable 94, 각각 95이상 목표는 아직 미달. 두 평가 모두 종료.** [원문·수용·실행 근거](docs/reviews/2026-10-23-artifact-r5.md). 면접·개인 역량 평가는 제외합니다.
- 각 평가자가 새 사본/venv에서 140통과·14제외, 격리 PostgreSQL/MinIO 13통과, 합성 7일 실패 보존/재처리·34개 파일 SQLite 복원을 실행했습니다. 호스트 symlink 1건 제외, 서비스 13건은 별도 실행. 원본 점수와 후속 정정은 구분합니다.
- 2026-10-23 **20:59 KST 읽기 확인**: Compose app-db/minio/dashboard는 Exited(255), 8502 health/ready 연결 거부. kind 6개 서비스 Pod Ready, 관리 8504·별도 랜딩 8507 listening. Compose Airflow 3개는 Created/중지. 이번 인계에서 시작·종료하지 않았습니다.
- [대시보드8502](http://127.0.0.1:8502/?view=overview&period=2024-04&source=public)는 현재 중지. 재시작: `docker compose --env-file .env -f infra/compose/compose.yaml start app-db minio dashboard` 후 `/ready` 확인. [운영 절차](docs/runbooks/operator.md#8502가-열리지-않을-때). 관리 8504는 `scripts/ops/admin.ps1 stop`으로 별도 종료합니다.
- kind ONS의 마지막 확인 설정은 매일 14:00 KST 활성, 다른 6개 DAG paused. 이번 인계에서는 Pod만 재확인했고 새 scheduled 실행은 확인하지 않았습니다. [일정 on/off](docs/runbooks/dags.md#ons-정기-수집-켜기끄기).
- 공개 BR-PVGen 전체 51발전소/12,572일 v2는 Compose, kind의 BR 자료는 PS_001 하루, native는 v1 보존본. ONS의 기존 검증 범위는Compose 69,696행/21일·kind 167,424행/51일. 환경별 저장소는 독립입니다. [수집 근거](docs/benchmarks/incremental-v0.5.0.md).
- 추정 kWh·검토 후보·누락/무효/보간을 구분합니다. ONS 원문 MWmed·시간 기준 미확정을 보존하고 기존 kWh에 합산하지 않습니다. 고객·매출·외부 SLO·장기 쓰기 부하는 미검증입니다.
- [독립 랜딩 v6](http://127.0.0.1:8507/) 완료. 히어로 카드를 실제 공개 집계 기반 데모 창(전체 현황/월간 보고서/원본 계보)으로 교체, 보고서 문서형·계보 4단계 흐름, CSS 재작성. 1440/768/375 렌더·axe위반0, 미검증 범위는 [작업 기록](docs/worklog/2026-10-23-landing.md#v6-히어로-실제-데모-창과-전체-다듬기)·[QA](landing/QA.md). [실행](landing/README.md). 별도 loopback 정적 서버이며 FastAPI는 이 작업에서 변경하지 않았습니다.

## 다음 재개 지점

1. AGENTS.md → 이 문서 → [plan.md](plan.md) → [R5 인계 상세](docs/worklog/2026-10-23-handoff-r5.md)를 읽습니다. INT-05(19점) → DOC-06(16점) → REVIEW-02(16점) 순서이며 BIZ-01은 사용자 요청으로 후순위입니다.
2. INT-05: Fable이 합성 지표의 `interpolation_unknown_slots`를 제거해 보고서 KeyError를 재현했습니다. 실제 과거 v2 누락 여부·지원 계약부터 확인합니다. 현재 생성기는 해당 필드를 기록합니다. 원본 수정이나 무조건 0 대입은 하지 않습니다.
3. DOC-06: `migrations/0001_catalog.sql`에 ONS 3개 테이블·PG 인덱스 2개가 없는 정적 불일치. 실제 `db-migrate` 경로와 baseline의 범위를 맞춥니다. 운영 DB 변경부터 시작할 필요는 없습니다.
4. Astra의 org_id/hash 설명 오류는 계약·아키텍처·설계 사례·질문 4개 문서에서 정정했습니다. hash에는 org_id가 없고 조직 격리는 저장/조회 조건이 담당합니다. 계산·기존 자료 불변, 정정본 독립 확인은 미실행입니다.
5. 의미 있는 보완·관련 검사 뒤 동일 고정 커밋을 새 Astra/Fable에 제공합니다. 목표/이전 점수·상대 피드백은 평가자에게 주지 않습니다. Fable은 Claude Code `--model fable`, R5 실제 모델 `claude-fable-5-1`; Astra 요청 `gpt-6-astra`, resolved ID 미제공입니다.
6. 자동 점검 `solarops`는 10:00 KST 일정이나 **현재 PAUSED**. 이번 인계에서 변경하지 않았습니다. 진행 중인 독립 평가는 없으며 기존 R5를 중복 시작하지 않습니다.
7. Git 제외 `artifacts/artifact-review-r5-20261023/`에 고정 사본·UTF-16LE Fable stream·JUnit·합성 근거·실행기를 보존했습니다. 원문/요약은 docs/reviews에 게시합니다. 임시 `update-handoff.py`·과거 `record.py`/`finish.py`는 재실행하지 않습니다.
8. 별도 랜딩 세션의 `landing/`·이미지·skills-lock.json·.gitignore 및 공유문서 수정이 남아 있습니다. 이번 인계 커밋에서 제외했으며 전체 `git add .`·되돌리기·삭제를 하지 않습니다. 원본/ZIP/볼륨/과거 평가 보존, 민감한 삭제는 사용자 허락이 필요합니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-23 | 랜딩 v6 히어로 데모 창·보고서/계보 재구성, v5 HTML/SVG 제품 화면·세너비 검수 | [랜딩 구현·검수](docs/worklog/2026-10-23-landing.md) |
| 10-23 | R5 Astra 96 / Fable 94·원문 보존·hash 설명 정정·다음 세션 인계 | [인계·검증](docs/worklog/2026-10-23-handoff-r5.md), [R4 구현](docs/worklog/2026-10-23-quality-r5.md) |
| 10-23 | Fable·Astra 면접 평가·합성 경계 3개 재현·후속 21/19/16점 등록 | [평가·재현·전달](docs/worklog/2026-10-23-interview.md) |
| 10-23 | PORT-01~04완료·ONS상태UI·0.5.1배포·격리재현·제출자료·최신CI | [최종 수행](docs/worklog/2026-10-23-portfolio-finish.md) |
| 10-23 | ONS 실제 증분·정기 KPO·공개 DAG 동시 2개 비교, 0.5.0 배포·문서 갱신 | [수행·전달](docs/worklog/2026-10-23-incremental.md) |
| 10-23 | 입력/게시 4경계 수정·0.4.2 정렬·실제 KPO 재시도/추적·세 환경 7일 일치 | [구현·배포](docs/worklog/2026-10-23-integrity-delivery.md) |
| 10-23 | 독립 검토·경계 4개 재현·6개 후속 계획 | [수용 판단](docs/worklog/2026-10-23-independent-review.md) |
| 10-23 | 실제 수집/스케줄·환경별 아키텍처·README 정리 | [문서·상태](docs/worklog/2026-10-23-data-architecture.md) |

100줄 이내·최근 요약 최대 8개. 이전 handoff/discoveries는 [원문 보관](docs/worklog/archive/README.md)이며 현재 지침이 아닙니다.
