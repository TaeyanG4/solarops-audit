# 문서 안내

[프로젝트 홈](../README.md) · [현재 구현 상태](IMPLEMENTATION_STATUS.md)

처음 보는 사람은 시연 → 설계 근거 → 검증 결과 순서로 읽으면 구현과 주장의 범위를 함께 확인할 수 있습니다. 운영 명령은 설치 안내와 runbook에 두고, 과거 측정값은 검증 기록에 보존합니다.

| 목적 | 문서 |
|---|---|
| 5분 안에 실행 | [시연 순서](portfolio/DEMO_GUIDE.md), [설치·환경 변수](guides/setup.md) |
| 현재 진행도와 다음 과제 | [구현 상태](IMPLEMENTATION_STATUS.md), [점수 기반 계획](../plan.md), [인계·진행 기록](../handoff.md), [날짜별 상세 기록](worklog/README.md), [버전별 변경](../CHANGELOG.md) |
| 독립 기술 검토 | [독립 세션 평가](reviews/2026-10-23-independent.md), [재현·수용/보류 판단](worklog/2026-10-23-independent-review.md) |
| 포트폴리오 설명 | [한 쪽 제출 요약](portfolio/SUBMISSION.md), [설계 질문5개](portfolio/DESIGN_QUESTIONS.md), [문제·설계·증거 사례](portfolio/CASE_STUDY.md), [최종 검증](benchmarks/portfolio-finish-20261023.md) |
| 기술 선택 이해 | [버전·선택 이유·대안](architecture/technology-stack.md), [아키텍처·배포 경계·데이터 흐름·트랜잭션](architecture/system.md) |
| 실제 사용·자료 진위 | [실행 기술·원본 해시·독립 계산·합성 시험 구분](benchmarks/stack-authenticity-20261023.md) |
| 데이터 출처 | [제작자·범위·라이선스·파일 다운로드](data-sources.md), [ONS 시간별 계약·증분 수집 API](ons-source-contract.md) |
| 수집 주기·데이터 추가 | [실제 자동화 상태·처리 명령·새 출처 연동 범위](guides/data-ingestion.md) |
| 데이터 해석 | [실제 CSV 스키마·품질·에너지 계약](data-contract.md) |
| 로컬 운영 | [화면·보고서](runbooks/operator.md), [DAG·백필](runbooks/dags.md), [실패·진단](runbooks/recovery.md), [백업·복원 시험](runbooks/backup-restore.md) |
| 디자인·사용 스킬 | [새 디자인 시스템](../DESIGN.md), [워크스페이스·보고서·관리 검증](benchmarks/workspace-20261023.md), [스킬별 목적·결과물](development/skills.md), [최신 이미지](portfolio/images/workspace-20261023/README.md) |
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
- [0008: 보존 원본·읽기 전용 조회·보고서 동시성](adr/0008-storage-integrity.md)

최신 기술 후속 검증은 [선택형 서비스 CI·보고서 비교·독립 인스턴스 복원·동시 부하](benchmarks/technical-20261023.md), 저장·조회 경계는 [v0.4.1 무결성 기록](benchmarks/integrity-v0.4.1.md)을 확인합니다.

현재 UI: [방향과 추가 요건](design/workspace-navigation.md) · [전후 화면·검증 결과](benchmarks/workspace-20261023.md). 초기 전체 현황 개선은 [과거 검증](benchmarks/overview-redesign-20261023.md)으로 보존합니다.

`plan/`은 [원본 기획](plan/00_START_HERE.md)과 [SHA-256 목록](plan/MANIFEST.sha256)을 보존하는 영역입니다. 과거 예시 프롬프트·중단 조건·계획은 현재 실행 결과나 사용자의 현재 지시와 구별합니다. 최신 상태는 위 구현 상태 문서가 기준입니다.

최신 v0.5.0: [ONS 실제 정기 수집·Airflow 공개 병렬 측정](benchmarks/incremental-v0.5.0.md) · [릴리스 이미지](releases/0.5.0.json).
