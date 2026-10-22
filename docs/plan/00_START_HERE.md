# SolarOps Audit — Codex 전달 패키지

## 목표
데이터 엔지니어링 실무 포트폴리오와 **실제 유료 파일럿 시도**를 동시에 추진하는, 태양광 O&M 데이터 검증·월간 리포트 서비스의 실행 계획.

## 읽을 순서
1. `01_MASTER_PRD.md` — 사업가치, 실제 자료, 전체 아키텍처, 데이터 계약, DAG/K8s, 완료 기준, 12주 계획.
2. `02_CODEX_EXECUTION.md` — M0~M9 단계별 실제 구현·검증 지시, 복사해 사용할 Codex 프롬프트.
3. `03_BUSINESS_PILOT.md` — 실제 고객 검증, 가격 가설, 데이터 사용 허가와 계약, 매출 측정.
4. `04_REVIEW_SESSION_PROMPT.md` — **새로운 독립 Codex/ChatGPT 세션에서** 위 문서들을 비판적으로 검토하도록 요청하는 프롬프트.
5. `05_REVIEW_RESULTS.md` — 현재 수행한 문서 QA 및 남은 위험. (독립 모델 세션의 리뷰 결과는 별도로 기록.)

## 첫 실행
1. Windows에서 WSL2(Ubuntu) + Docker Desktop을 준비하고, Ubuntu의 `~/projects/solarops-audit`에 신규 Git 저장소를 생성한다.
2. 이 패키지의 `01_MASTER_PRD.md`와 `02_CODEX_EXECUTION.md`를 저장소 루트 또는 `docs/plan/` 아래에 복사한다.
3. Codex에서 `02_CODEX_EXECUTION.md`의 **D항 최초 프롬프트**를 실행한다.
4. **M0만 완료하고** 테스트/결과를 검토한다. M1 이후는 각각 별도의 요청으로 진행한다.
5. 본 구현은 아직 진행되지 않았다. 이 패키지는 구현 계획·검증 기준이므로 `make` 명령은 Codex가 해당 마일스톤에서 생성한다.

## 불변 조건
- Airflow + Kubernetes **둘 다 구현**한다. 다만 작은 실제 유료 서비스에 반드시 프로덕션 배포하지는 않는다.
- 공개 BR-PVGen 자료는 15분 집계/보간이 있는 역사 데이터이며 실제 라이브 API가 아니다.
- 발전량은 계량값이 아닌 근사치이며, 실제 고장 진단/금전 손실의 확정값을 제공하지 않는다.
- 대용량 파일 자동 다운로드, 고객 데이터 자동 업로드/공개, 비밀 하드코딩을 금지한다.
- 인터뷰·유료 파일럿 성사 여부와 코딩 성공 여부를 따로 평가한다.

## 자료 출처(2026-10-21 확인)
- https://zenodo.org/records/21511487
- https://zenodo.org/records/21511487/files/Readme.txt?download=1
- https://airflow.apache.org/docs/helm-chart/stable/quick-start.html
- https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/operators.html
- https://docs.docker.com/desktop/features/wsl/
- https://www.solarlog.kr/service/om
