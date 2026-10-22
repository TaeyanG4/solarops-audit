# SolarOps Audit — 진행 기록과 재개 지점

## Shared state

- Active agent(s): A
- Current project state: v0.3.1에서 계산 정확성·수익화 준비의 점수 기반 후속 작업 시작
- Current best: v0.3.1 / energy-interval-v1 (D-A-001)
- Active compute: local Windows Python 3.12 / WSL / Docker; 추가 에이전트 없음
- Open consistency issues: none
- Scoring: 0–3점씩 평가. Priority = 2×Impact + 2×Information + Confidence + Unblock + Diversity + (3−Cost), 최대24. 동점은 낮은 Cost, 높은 Information 순. 선행조건 미충족은 이유를 기록하고 다음 실행 가능 항목 진행.
- Initial order: H-A-01 21점 → H-A-02 20점 → H-A-03 19점 → H-A-04 17점 → H-A-05 17점 → H-A-06 16점(사용자 제공·승인 의존).
- Scope: 공개/합성 로컬 자료와 private GitHub. 고객 연락/데이터·외부 배포·결제는 이 작업에 포함하지 않음. 삭제는 승인 전 실행하지 않음.
- Coordination paths: 기존 AGENTS.md를 보존. Windows의 agents.md는 같은 파일로 해석됨; Linux는 AGENTS.md를 읽는다. 별도 대소문자 중복 파일을 만들지 않음.

## Active handoff

### Agent: A
- Current host: Codex
- Current thread: H-A-02
- Resumable state: v2 서비스 전체 비교 완료, Compose/kind 0.4.0 적용. 실제 Compose 합성/kind 공개 DAG 검증 실행 중. H-A-03/04/05 완료; 브라우저·패키징·CI 결과를 H-A-02에 기록 예정.
- Blocker: none
- Next action: H-A-02, H-A-06(승인 표본 의존), H-A-07

## Completed / review log

### 2026-10-22 22:48 — A — none
- Host: Codex
- Action: 사용자 요청에 따라 점수 기반 계획·발견·인계 체계를 초기화하고 직전 수익화 판단을 기록.
- Result: 기존 기술 근거와 사업 가정 분리; see D-A-001
- Artifacts: plan.md, discoveries.md, handoff.md, AGENTS.md
- Discovery updates: D-A-001
- Review verdict: none
- Resource: CPU
- Other executor: none
- New plan items: H-A-01, H-A-02, H-A-03, H-A-04, H-A-05, H-A-06

### 2026-10-22 22:53 — A — H-A-01
- Host: Codex
- Action: 경계 fixture 재현 후 계산 v2와 결과 해시를 수정. 완료 항목을 계획에서 제거하고 H-A-02 선행조건 해소.
- Result: 경계 수정·회귀 통과; see D-A-002
- Artifacts: tests/test_calculation_v2.py, src/solarops/analytics/metrics.py, src/solarops/pipeline.py, src/solarops/config.py, artifacts/calculation-v2-before.log, artifacts/calculation-v2-after.log
- Discovery updates: D-A-002
- Review verdict: none
- Resource: CPU
- Other executor: none
- New plan items: none — H-A-02가 전체 비교·배포를 이미 포함

### 2026-10-22 23:02 — A — H-A-03
- Host: Codex
- Action: 서비스 재처리 대기 중 독립적인 파일럿 범위·원가 기록 완료. H-A-06 점수 유지.
- Result: 완료 근거 기록; see D-A-003
- Artifacts: docs/market/revenue-assessment.md, docs/market/pilot-scorecard.md, docs/market/pilot.md
- Discovery updates: D-A-003
- Review verdict: none
- Resource: CPU
- Other executor: none
- New plan items: none — 후속 고객 검증은 H-A-06, 배포는 H-A-02가 포함

### 2026-10-22 23:02 — A — H-A-04
- Host: Codex
- Action: 서비스 재처리 대기 중 진단 CLI 구현과 SQLite/PostgreSQL 확인 완료.
- Result: 완료 근거 기록; see D-A-004
- Artifacts: src/solarops/diagnostics.py, src/solarops/cli.py, tests/test_diagnostics.py, artifacts/inspect-runs-v040.json
- Discovery updates: D-A-004
- Review verdict: none
- Resource: CPU
- Other executor: none
- New plan items: none — 후속 고객 검증은 H-A-06, 배포는 H-A-02가 포함

### 2026-10-22 23:12 — A — H-A-05
- Host: Codex
- Action: 독립 합성 백업·복원 도구/운영 계약 작성과 실제 왕복 시험 완료. 서비스 복원 검증은 별도 H-A-07(15점)로 분리하고 H-A-06(16점, 승인 의존)은 유지.
- Result: 로컬 복원 범위 확인; see D-A-005
- Artifacts: scripts/validation/backup_restore_drill.py, docs/runbooks/backup-restore.md, data/restore-v040-verified/evidence.json, data/restore-v040-verified/backup-manifest.json, artifacts/restore-v040.log
- Discovery updates: D-A-005
- Review verdict: none
- Resource: CPU
- Other executor: none
- New plan items: H-A-07
