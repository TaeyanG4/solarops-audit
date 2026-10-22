# 인수 상태

현재 사용자 요청은 전체 구현입니다. 원본 ZIP은 유지하고 단계별 예시 중단 지시는 요청 범위로 취급하지 않았습니다.

| 단계 | 구현과 검증 |
|---|---|
| M0 | Python 3.12/uv.lock, CLI, lint/test, Make, CI 설정, Git 골격 |
| M1 | Zenodo 실제 4파일, MD5/SHA-256, metadata/양 ZIP의 실제 컬럼·ID·단위 확인, 경로/용량 안전 검사 |
| M2 | 원본 보존, 청크/하루 단위 Parquet, 조직/버전, PostgreSQL·MinIO, 원자적 active manifest |
| M3 | 에너지 근사, missing/invalid/interpolated 구분, 신뢰도 기반 검토 후보, 월간 HTML/CSV/계보 |
| M4 | Compose 스택 실제 실행, 앱 DB/메타 DB 분리, 무작위 로컬 secret |
| M5 | 4 DAG import 및 정상/실패재시도/백필/품질/보고서 실제 실행 |
| M6 | kind+Helm, KPO 실제 Pod 실행, 내부 서비스 DNS, 전용 SA와 리소스 한도 |
| M7 | 3회 재실행, 트랜잭션 rollback, Pod 종료 복구, 1/2/4 Pod 측정, 공개 전체 처리 |
| M8 | 읽기 전용 UI/API, 실제 브라우저 확인, 운영·복구 문서 및 데이터 인용 |
| M9 | 스키마 매핑/인터뷰/제안/비식별 체크/가격 계산 준비. 인터뷰·계약·결제는 미실행 |

테스트/실행의 정확한 수치와 범위는 `docs/benchmarks/2026-10-22.md`에 정리합니다. 원본 실행 로그는 gitignored `artifacts/`에 남습니다. 비공개 [GitHub 저장소](https://github.com/TaeyanG4/solarops-audit)와 원격 CI를 연결했습니다. 독립 외부 세션 리뷰·실제 현장 고장 라벨 검증·공개 서비스 배포는 수행하지 않았습니다.

v0.2.0: Airflow Params에 공개/합성 자료 및 발전소 선택을 추가했습니다. 공통 `replay` CLI는 기본 계획 확인, 최대 31일, 원본 경로/발전소/관측 범위 검사를 수행합니다. 품질·월간 보고서도 같은 발전소/자료 종류로 제한합니다. Compose는 원본을 읽기 전용 마운트하고 kind는 체크섬과 덮어쓰기 방지로 원본을 준비합니다.

v0.3.0: 단일 쿼리의 월별 현황 API와 슬롯 가중 집계, 반응형 대시보드, 최신순·상태별 실행 이력, batch→partition 연결을 추가했습니다. 이전 실행 기록은 추측해서 채우지 않습니다. 독립 합성 복구 데모, OS별 CI 아티팩트, [포트폴리오 사례](portfolio/CASE_STUDY.md)와 [5분 시연](portfolio/DEMO_GUIDE.md)을 제공합니다. [조회 성능·검증 조건](benchmarks/workspace-v0.3.0.md)을 함께 기록했습니다.

의도한 제약: 단일 로컬 조직 접근, 역사 데이터의 고정 구간 재처리, 고객 CSV 자동 업로드 불가, 일별 사건 경계 병합 없음, 실패 staging/작업 Pod 보존, 알림/결제/고객 인증 미구현. 후속 범위는 중단된 실행 상태의 자동 조정과 보존·백업 정책, 승인된 고객 스키마 어댑터이며 고객 연결은 실제 승인·사업 검증 이후입니다.
