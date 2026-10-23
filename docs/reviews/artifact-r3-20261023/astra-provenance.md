# Astra R3 평가 provenance

- 일자/시간대: 2026-10-23, Asia/Seoul. focused pytest 시작 18:19:17 KST, 데모 보고서 생성 18:19:38 KST.
- 작업 루트: `H:/dev/solarops_audit`.
- 독립 평가 세션: `/root/astra_artifact_r3`, 부모 세션의 과거 대화 없이 새 작업(`fork_turns=none`).
- 생성 호출의 지정 모델: `gpt-6-astra`, `reasoning_effort=high`. 메인 조정자가 생성 설정을 확인했다. 실제 서비스 내부 모델 버전을 별도 API로 조회한 것은 아니다.
- 실제 확인한 Git HEAD: `36ac6ff937b06a481988d9264c65ac1a9597a59a`.
- 앱/계산: 0.5.4 / energy-interval-v2.
- `docs/releases/0.5.4.json`의 구현 SHA: `93ad341219de368068a22cb347ca74b8f43f6130`.
- `git diff 93ad341219de368068a22cb347ca74b8f43f6130 HEAD --stat -- src dags infra scripts pyproject.toml uv.lock` 결과 출력 없음. 검토 마지막의 해당 구현/검사 경로 status도 수정 없음.
- README는 시작 당시 clean 상태에서 읽었다. 검토 중 별도 작업이 README에 landing 소개를 추가했음을 후반 status와 조정자 안내로 확인했다. 새 문단/링크 내용은 읽지 않았으며 처음 읽은 고정 커밋 README만 평가했다.

## 독립성/제외 경계

AGENTS.md 다음에 고정 rubric만 읽었고, 이번 독립 검토 지시의 blind 범위를 우선했다. `handoff.md`, `plan.md`, 다른/이전 평가 원문·점수·수용 판단, 다른 평가자 결과, 이전 review artifacts, 다른 worklog(유일한 예외는 아래 bounds 재현 문서), `.env`, `infra/generated`, 사용자 전역 설정, `.gitignore`/`skills-lock.json` 변경 내용, `.taste-skill`, `landing/` 및 landing docs/images는 읽지 않았다. 현재 문서 안의 과거 리뷰 링크 제목이 보인 것은 있으나 링크를 따라가거나 점수를 찾지 않았다. 목표 점수는 제공받거나 찾지 않았다.

첫 `git status --short`는 제외된 작업 경로의 이름만 출력했다. 이 경로들을 검색·열람하지 않았다. 파일 목록 탐색은 지정 `src`, `tests`, `scripts/release`, `scripts/demo`, `docs/architecture`, `docs/runbooks`, `docs/benchmarks`, `.github`, `infra`에 한정했고 `infra/generated`는 제외했다. 프로젝트 전체 텍스트 검색은 하지 않았다.

## 실제 읽은 범위

전체 파일 내용을 읽은 주된 파일:

- 규칙/평가: `AGENTS.md`, `docs/reviews/portfolio-rubric.md`.
- 도입/계약: `README.md`, `docs/data-contract.md`, `docs/ons-source-contract.md`.
- 구조/운영/시연: `docs/architecture/system.md`, `docs/architecture/technology-stack.md`, `docs/runbooks/recovery.md`, `docs/runbooks/backup-restore.md`, `docs/guides/setup.md`, `docs/portfolio/DEMO_GUIDE.md`, `docs/portfolio/SUBMISSION.md`, `docs/portfolio/CASE_STUDY.md`.
- 처리/저장: `src/solarops/pipeline.py`, `replay.py`, `config.py`, `runtime.py`, `cli.py`, `diagnostics.py`, `normalize/parquet.py`, `analytics/metrics.py`, `contracts/brpvgen.py`, `acquisition/ons.py`, `storage/minio.py`, `storage/postgres.py`.
- 보고서/API/관리: `src/solarops/reports/render.py`, `reports/freshness.py`, `api/app.py`, `api/readmodels.py`, `admin/app.py`.
- 검사: `tests/conftest.py`, `tests/test_contracts.py`, `test_pipeline.py`, `test_calculation_v2.py`, `test_publication_boundaries.py`, `test_integrity_boundaries.py`.
- 빌드/실행 정의: `pyproject.toml`, `src/solarops/release.json`, `scripts/release/release.py`, `scripts/demo/portfolio_demo.py`, `dags/solarops_factory.py`, `infra/docker/Dockerfile`, `infra/docker/Dockerfile.minio`, `infra/compose/compose.yaml`, `.github/workflows/ci.yaml`, `.github/workflows/services.yaml`.
- 역사 증거: `docs/releases/0.5.4.json`, `docs/benchmarks/quality-v0.5.4.md/json`, `quality-v0.5.3.md`, `technical-20261023.md`, `incremental-v0.5.0.md`, `stack-authenticity-20261023.md`, `integrity-v0.4.2.md`.
- 유일하게 허용된 worklog: `docs/worklog/2026-10-23-bounds-reproduction.md`.

부분/요약 확인:

- `uv.lock` 앞 30줄의 Python 요구와 package hash 구조; release check가 전체 TOML을 파싱해 프로젝트 버전을 검사했다.
- `infra/docker/airflow-constraints-3.12.txt`의 Airflow/KPO 버전 줄 검색; release check가 파일 전체 SHA를 검증했다.
- `docs/benchmarks/technical-20261023.json` 첫 70줄의 조건별 표본/p50/p95/errors 구조. 원시 지연이나 JSON 전체를 재집계하지 않았다.
- 초기 여러 문서의 묶음 출력이 일부 잘렸으므로 `system.md`는 이후 전체를 별도 재확인했다. 코드를 근거로 지목한 경계는 해당 코드 전문과 줄 번호를 확인했다.
- 평가자 자신의 생성 결과 `evidence.json`에 해당하는 데모 stdout, pytest stdout/XML, release stdout.

문서에 연결된 `data-sources.md`, ADR, operator/dags runbook, 그 외 benchmark/전체 worklog, 대시보드 JS/CSS/이미지, 실제 PostgreSQL·MinIO·Airflow 카탈로그, 보존 공개 CSV는 읽었다고 주장하지 않는다. 일부는 파일 목록/링크 제목만 보였다.

## 실행한 도구/명령

도구는 `functions.exec`를 통한 `exec_command`(PowerShell), 실행 중 pytest의 `write_stdin`, 결과 문서 저장의 `apply_patch`, 조정자와의 `collaboration.send_message`만 사용했다. 새 하위 에이전트나 사용자 소유 chat을 만들지 않았다.

검사 명령과 정확한 출력 파일:

```text
.venv/Scripts/python.exe -m pytest tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py -q --basetemp artifacts/astra-r3-pytest-20261023 --junitxml artifacts/artifact-review-r3-20261023/astra-pytest.xml
# 79 passed in 24.60s; JUnit: tests=79 errors=0 failures=0 skipped=0 time=24.601

.venv/Scripts/python.exe scripts/demo/portfolio_demo.py --output artifacts/astra-r3-synthetic-20261023
# active_partitions=7; failure preservation=true; replay equality=true

.venv/Scripts/python.exe scripts/release/release.py check
# Release declarations aligned: 0.5.4

.venv/Scripts/python.exe --version
# Python 3.12.13
```

명령 stdout/stderr는 PowerShell `Tee-Object`로 각각 `astra-pytest.txt`, `astra-demo.txt`, `astra-release.txt`에 보존했다. pytest는 한 번만 실행했고 전용 새 basetemp를 사용했다. 최초 제공된 `test_energy_v2.py`는 실제 파일이 없음을 보고했고 조정자가 `test_calculation_v2.py`로 대체를 명시 승인했다.

원본/서비스/기존 산출물에 쓰지 않았다. 새로운 전용 pytest·데모 출력과 이 평가 폴더에만 썼다. 영구 테스트/검증 스크립트 추가, 삭제, 설치, 네트워크 fetch, 인프라 변경, 공개 전체 처리, git commit/push를 수행하지 않았다. 기존 집중 테스트 자체는 전용 임시 fixture에 손상·실패를 주입하며 그 임시 자료도 남긴다.

## 역사 증거의 취급

v0.5.4의 전체140통과·14제외, 실제 PostgreSQL/MinIO13통과, CI 양OS 성공, Compose/kind 업데이트와 내용 hash 보존은 저장소가 제공한 작성자 증거다. 이번 평가자가 라이브 서비스나 GitHub를 조회해 독립 재실행한 사실이 아니다. v0.5.0 ONS 수집/KPO 병렬 측정, v0.4.2 환경 동등성/재시도, 전체 공개 처리/대표 독립 계산, 복원·부하 측정도 동일하게 과거 증거로 구분했다.

현재 코드의 작은 계약·실패 경계는 이번 79개 검사와 새 데모로 직접 확인했다. 새 환경 설치와 전체 인프라 재빌드·부하 재현은 허용 범위 밖에서 확대하지 않았다. handoff/plan을 배제한 상태이므로 프로젝트 전체 미완료 목록의 완결성을 판단하지 않았다.
