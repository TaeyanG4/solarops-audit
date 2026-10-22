# 문서 안내

[프로젝트 홈](../README.md) · [현재 구현 상태](IMPLEMENTATION_STATUS.md)

처음 보는 사람은 시연 → 설계 근거 → 검증 결과 순서로 읽으면 구현과 주장의 범위를 함께 확인할 수 있습니다. 운영 명령은 설치 안내와 runbook에 두고, 과거 측정값은 검증 기록에 보존합니다.

| 목적 | 문서 |
|---|---|
| 5분 안에 실행 | [시연 순서](portfolio/DEMO_GUIDE.md), [설치·환경 변수](guides/setup.md) |
| 현재 진행도와 다음 과제 | [구현 상태](IMPLEMENTATION_STATUS.md), [점수 기반 계획](../plan.md), [인계·진행 기록](../handoff.md), [결과 근거](../discoveries.md), [버전별 변경](../CHANGELOG.md) |
| 포트폴리오 설명 | [문제·설계·증거 사례](portfolio/CASE_STUDY.md) |
| 기술 선택 이해 | [버전·선택 이유·대안](architecture/technology-stack.md), [폴더·데이터 흐름·트랜잭션](architecture/system.md) |
| 데이터 해석 | [실제 CSV 스키마·품질·에너지 계약](data-contract.md) |
| 로컬 운영 | [화면·보고서](runbooks/operator.md), [DAG·백필](runbooks/dags.md), [실패·진단](runbooks/recovery.md), [백업·복원 시험](runbooks/backup-restore.md) |
| 검사·패키징·기여 | [개발 안내](../CONTRIBUTING.md), [스크립트 목록](../scripts/README.md) |
| 실행 증거 | [공개 전체 처리·Compose·kind](benchmarks/2026-10-22.md), [v0.3 화면·조회 성능](benchmarks/workspace-v0.3.0.md), [v0.3.1 유지보수](benchmarks/maintenance-v0.3.1.md), [v0.4 계산·진단·복원](benchmarks/reliability-v0.4.0.md) |
| 파일럿 준비 | [수익화 판단](market/revenue-assessment.md), [제안과 범위](market/pilot.md), [측정 양식](market/pilot-scorecard.md), [인터뷰 양식](market/interview-template.md), [스키마 대응표](market/schema-mapping.csv) |

## 설계 결정 기록

- [0001: 일별 Python/Arrow 처리와 DuckDB](adr/0001-data-processing.md)
- [0002: Compose와 kind의 독립 저장소](adr/0002-two-environments.md)
- [0003: LocalExecutor와 KubernetesPodOperator의 역할](adr/0003-kpo-not-executor.md)
- [0004: 데이터 품질·추정 에너지](adr/0004-data-quality.md)
- [0005: 사업 범위](adr/0005-business-scope.md)
- [0006: 월별 조회 모델](adr/0006-workspace-read-models.md)
- [0007: 계산 v2와 기존 결과 보존](adr/0007-calculation-v2.md)

`plan/`은 [원본 기획](plan/00_START_HERE.md)과 [SHA-256 목록](plan/MANIFEST.sha256)을 보존하는 영역입니다. 과거 예시 프롬프트·중단 조건·계획은 현재 실행 결과나 사용자의 현재 지시와 구별합니다. 최신 상태는 위 구현 상태 문서가 기준입니다.
