# SolarOps Audit — 결과와 판단 근거

`PENDING`은 다른 호스트의 독립 검토가 없다는 뜻입니다. 자체 실행의 통과/실패는 Evidence에 별도로 기록하며 검토 완료를 꾸며내지 않습니다.

## D-A-001 — v0.3.1 기준과 수익화 판단
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 기술 MVP와 로컬 배포 검증은 확보했지만 실제 수요·매출·고객 파일 정확성은 미검증이다. 첫 수익 경로는 검수형 보고서 파일럿이며 SaaS 셀프서비스는 후속이다.
- Evidence: docs/benchmarks/maintenance-v0.3.1.md, docs/IMPLEMENTATION_STATUS.md, docs/market/pilot.md; 사용자와 2026-10-22 논의. 20만원 매출·시급2.5만원·직접비2만원 가정이면 4시간시 8만원, 12시간시 -12만원. 세금/영업/초기개발/고정비 제외이며 시장가격/매출 실적이 아님.
- Implication: new current best: 배포 기준 v0.3.1 / energy-interval-v1; 계산 경계 수정과 고객별 수작업 측정을 먼저 진행한다.
- Reviews:

## D-A-002 — v2 계산 경계와 해시 회귀
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 모두 무효인 전력 슬롯은 null, 실제 0은 0, 일부 유효 슬롯은 유효값 합으로 구분한다. 현지 일자의 UTC 구간과 원본 범위의 교집합으로 공개를 판단하면 UTC±경계의 불필요한 빈 파티션이 사라진다.
- Evidence: tests/test_calculation_v2.py; artifacts/calculation-v2-before.log의 4실패(3개 결함 재현+1개 v2 요건), artifacts/calculation-v2-after.log의 관련18개 통과. 전체 Windows 88 passed,2 skipped. 시계열·품질·후보도 v2 논리해시에 포함하고 반복 해시 일치를 검사. DST 23/25시간 누락일은 92/100슬롯 유지.
- Implication: H-A-01 완료. v1 결과는 수정하지 않고 별도 v2 적재·일별 수치 비교 후 배포해야 함. 전체 데이터/서비스 전환은 H-A-02에서 검증한다.
- Reviews:

## D-A-003 — 유료 파일럿 범위·원가와 미검증 항목
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 초기 연동 비용과 반복 납품 비용을 분리하고 발전소 1–3개/한 형식/한 달/수정 1회로 범위를 제한하면 실측 가능한 판매 실험이 된다. 고객 수요나 수익이 확인된 것은 아니다.
- Evidence: docs/market/revenue-assessment.md, docs/market/pilot-scorecard.md, docs/market/pilot.md. pilot_price.py 실제 두 실행은 4시간 80,000원, 12시간 −120,000원. 손익분기 7.2시간은 입력 가정의 산술이며 실적이 아님. 측정 양식은 미측정 상태.
- Implication: H-A-03 완료. 실제 승인 표본·구매 의사 검증은 H-A-06에 유지하며 Confidence 0/16점 유지.
- Reviews:

## D-A-004 — 읽기 전용 미완료 실행 진단
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 조직별 running/validated 실행의 나이와 active 연결을 상태 변경 없이 조회한다. 오래됨/시간 누락/미래 시각은 검토 후보이며 프로세스 종료의 증거는 아니다.
- Evidence: tests/test_diagnostics.py 7개 통과: org 격리, timestamp, pagination, active 자식, SELECT만 실행, DB 비변경, 없는 SQLite 생성 금지, 실제 readonly SQLite. artifacts/inspect-runs-v040.json은 실제 PostgreSQL 실행중 batch 1개를 within_threshold로 확인.
- Implication: H-A-04 완료. 자동 실패/삭제/재시도는 추가하지 않는다. 작업 생존 여부와 함께 운영자가 판단하는 절차를 runbook에 문서화한다.
- Reviews:

## D-A-005 — 합성 로컬 자료의 별도 경로 복원
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 쓰기가 끝난 합성 SQLite/로컬 파일은 DB snapshot과 파일별 SHA를 보존해 별도 경로로 복원할 수 있다. 원본 보고서는 바이트 그대로, 복원 catalog만 경로를 재배치한다. 서비스 DB/객체의 동시 백업까지 검증한 것은 아니다.
- Evidence: scripts/validation/backup_restore_drill.py, data/restore-v040-verified/evidence.json, backup-manifest.json. 7개 활성 파티션/DB 포함31파일, integrity ok, 손상 사본 거부, 복원 API/과거 보고서/원본 재처리 해시/새 보고서 확인. 최초 URL 오타 실패 로그 artifacts/restore-v040.log도 보존.
- Implication: H-A-05의 별도 합성 복원 시험 완료. PostgreSQL/MinIO의 생산자 일관성 경계와 격리 복원은 H-A-07에서 별도 검증한다.
- Reviews:

## D-A-006 — PostgreSQL·MinIO 합성 논리 복원
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 생산 완료된 합성 서비스 자료는 같은 서버의 별도 DB/버킷에 pg_dump와 객체 파일을 복원하고 카탈로그 버킷 URI를 재배치해 조회·보고서·재처리할 수 있다. 별도 호스트 재해복구/동시 생산자/RTO·RPO 보장은 아니다.
- Evidence: scripts/validation/service_restore_drill.py; data/service-restore-v040-verified/evidence.json, data/service-restore-v040-verified/backup-manifest.json. 7개 파티션/27객체, 전체 원본 catalog hash와 객체 SHA 보존, 과거 보고서 바이트·복원 raw 재처리 해시 일치. pg_dump16.10/이미지ID 기록. 복원~API 0.797초, 전체3.578초는 소규모 단일 로컬 측정. 모든 생성 DB/버킷/파일 보존.
- Implication: H-A-07의 격리 논리 복원 완료. 고객 도입 시 별도 호스트/저장소·RTO/RPO·보관 계약은 H-A-06의 실제 요구에 맞춰 범위를 정한다.
- Reviews:

## D-A-007 — 공개 v2 전환·실제 배포·기능 CI
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 서비스 공개 51개 발전소의 v2 적재와 기존 v1 보존을 검증했다. 12,572개 일별 지표/원본 SHA 일치, 31개 시계열 표본 2,976슬롯 중190개 0→null 수정 외 차이 없음. Compose/kind 0.4.0 배포와 기능 CI 성공.
- Evidence: docs/benchmarks/reliability-v0.4.0.md; artifacts/public-v1-v2-comparison.json. Windows95/WSL96 오프라인, 서비스1개 통과. Compose 합성/kind 공개 각5시나리오 성공, 재시도 try2 확인, 각4DAG pause. 브라우저 PS_001 4월 v2 보고서/오류0 확인. 기능26fdaef CI39794062156 성공(양OS96 passed,1skipped). 서비스 복원 후속18cdf64 CI39794977186 및 인계aa1ca86 CI39795527411도 success 확인.
- Implication: new current best: v0.4.0 / energy-interval-v2 로컬 배포 및 기능 CI 검증. H-A-02의 후속 CI까지 완료; 실제 수익성은 D-A-003/H-A-06의 별도 검증.
- Reviews:

## D-A-008 — 계보·읽기·동시성 결함 재현
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 기록한 원본 이후 입력이 바뀌면 다른 내용으로 결과가 생성되고, SQLite 동시 요청이 서로 다른 내용을 같은 source_version으로 둘 다 커밋한다. metadata 중복/폭 불일치도 통과한다. readiness는 없는 bucket을 생성하고 누락 보고서 파일은 비제어500이다.
- Evidence: tests/test_integrity_boundaries.py, artifacts/integrity-audit-before.log: 7 failed(메타데이터3, 입력변경1, 읽기부작용1, 누락파일1, 동시성1). 전용 합성 fixture와 fake S3만 사용, 사용자 원본 비변경.
- Implication: H-A-09 계보/버전22점, H-A-10 읽기API21점, H-A-11 나머지 계산·의존성·배포감사19점으로 후속 분리. 계산식 변경은 아직 없음.
- Reviews:

## D-A-009 — 보존 원본 처리와 버전 claim
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 처리 입력을 보존 원본으로 고정하고 source_version을 INSERT ON CONFLICT DO NOTHING으로 확보하여 입력 변경 및 같은 버전의 내용 덮어쓰기를 막았다. 메타데이터 중복 열/행 폭 오류도 거부한다.
- Evidence: tests/test_integrity_boundaries.py의 관련5개와 기존 pipeline/calculation18개 통과, tests/test_services.py 실제 PostgreSQL 동시 버전 포함2개 통과. artifacts/integrity-audit-after-source-verified.log, artifacts/service-integrity-v050.log.
- Implication: H-A-09 완료. 정상 계산 v2는 유지. 같은 로컬 raw 경로의 복사 도중 접근 경계는 H-A-11에서 추가 검사한다.
- Reviews:

## D-A-010 — 조회 부작용 제거와 파일 무결성
- Source: A
- Host: Codex
- Cross-check: PENDING
- Finding: 조회 API는 DB/테이블/버킷을 만들지 않는다. 없는 catalog/불완전 schema는503, 없는 파일은404, 새 SHA가 다른 파일은503으로 반환한다. SHA가 없는 기존 산출물은 계속 읽으며 소급 검증을 주장하지 않는다.
- Evidence: tests/test_integrity_boundaries.py 10 passed, tests/test_services.py 2 passed. SQLite 쓰기 거부·DB 미생성·누락 schema·파일 변조·legacy 호환과 실제 PostgreSQL transaction_read_only=on 및 UPDATE 거부/MinIO series 조회를 확인했다.
- Implication: H-A-10 완료. 설치 시 db-migrate/적재가 먼저 필요하며 H-A-11 릴리스 문서에 명시한다.
- Reviews:
