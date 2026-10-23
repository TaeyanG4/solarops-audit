# Astra R4 평가 provenance

- 날짜: 2026-10-23 Asia/Seoul.
- 요청된 모델/effort: `gpt-6-astra` / `high` (상위 세션의 독립 평가 위임에 명시). 본 세션은 해당 요청으로 생성된 Astra 평가 subagent다. 실행 모델 문자열을 별도 서비스 API로 조회할 수 있는 도구는 사용하지 않았으므로 모델 요청과 외부 검증을 혼동하지 않는다.
- 평가 대상: `954a421af31c34d14be99f0354ab783e4d18dec7`.
- 앱/계산: `0.5.5` / `energy-interval-v2`.
- 구현 이미지 릴리스 커밋: `cedf70216add558956001140c56b6931c40a1198` (`docs/releases/0.5.5.json`). 이미지 빌드 자체를 이번에 실행하지 않았다.
- 입력 사본: `H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/source`.
- 입력 manifest의 git-archive SHA256: `dcc2396ebeefc537a421dbb4115adb9099a4dcd8b6dc256ee07a58e2f65d6360`, 허용 tracked 파일 296개. `REVIEW_SNAPSHOT.json`을 읽었다. 원 archive를 독립 재해시하지 않았다.
- 고정 rubric: 입력 사본의 `docs/reviews/portfolio-rubric.md`.
- 출력 원문: `H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/astra-review.md`.
- 출력 provenance: 이 파일. 이후 원문의 평가/점수를 사후 편집하는 절차는 시행하지 않았다.

## 독립성·읽은 범위

AGENTS.md를 먼저 읽고 rubric/스냅샷 manifest를 읽었다. 명시적 blind scope에 따라 handoff.md와 plan.md는 읽지 않았다. 다른 평가 원문/점수, Fable 결과, 원본 mutable 저장소, 원본 서비스/데이터는 읽지 않았다. 기존 Python 실행 파일만 위임대로 재사용했다.

README, 데이터/ONS 계약, architecture/system 및 technology-stack, ADR0008, 구현 상태, recovery/backup-restore runbook, 최신/관련 benchmark 문서, bounds-reproduction worklog 한 개, 0.5.5 release JSON, pyproject/lock의 릴리스 검사, Dockerfile/MinIO Dockerfile, 두 CI workflow를 읽었다. benchmark 문서는 현재 동작의 보증이 아닌 역사적 증거로 다뤘다. 일부 큰 묶음 출력은 잘렸으며 이를 전 파일 정독으로 주장하지 않는다.

구현은 pipeline, normalize/parquet, contracts/brpvgen, analytics/metrics, acquisition/ons, storage/postgres 및 minio, reports/render 및 freshness, api/app 및 readmodels, config, cli, fixtures, admin/app와 services의 경계 부분, DAG factory, 지정 tests 및 services tests를 검토했다. UI 디자인 감사가 아니라 데이터/API/보고서 계약 검토였다. 화면 브라우저는 실행하지 않았다.

도구: `functions.exec`를 통한 PowerShell `exec_command`, `write_stdin`, `apply_patch`. 조회는 Get-Content/rg, 검사는 아래 Python/pytest 명령, Docker는 허용 probe의 새 컨테이너 및 그 이름의 상태 확인만 사용했다. 네트워크 데이터 다운로드·외부 메시지·원본 서비스 조작은 없었다. 공개 source/제품 코드/영구 tests를 수정하지 않았다.

## 모든 Python 명령에 적용한 환경

```powershell
$env:PYTHONPATH='H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/source/src'
$env:SOLAROPS_BUILD_REVISION='954a421af31c34d14be99f0354ab783e4d18dec7'
```

모든 Python 명령의 cwd는 `H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/source`, 실행 파일은 `H:/dev/solarops_audit/.venv/Scripts/python.exe`였다. 서비스 driver의 자식 pytest도 동일 env를 상속했다.

1. `-c "import solarops,sys; print(sys.version); print(solarops.__file__)"`
   - Python `3.12.13`; import: `H:\dev\solarops_audit\artifacts\artifact-review-r4-20261023\source\src\solarops\__init__.py`.
2. `-m pytest tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py -q --basetemp artifacts/astra-r4-pytest --junitxml artifacts/astra-r4-pytest.xml`
   - 최초 실행: 26 passed / 53 setup errors / 2.09s. `artifacts` 상위 폴더가 없어 WindowsPath.mkdir 실패. 제품 실패로 분류하지 않음.
   - 최초 JUnit만 `artifacts/astra-r4-pytest-initial-setup-error.xml`로 이동·보존. 출력 폴더 생성 후 동일 명령 1회 재실행: **79 passed / 34.08s**.
3. `H:/dev/solarops_audit/artifacts/artifact-review-r4-20261023/service-probe.py artifacts/astra-r4-services`
   - 실행 전 허용 probe 전문을 읽음. 기존 `tests/test_services.py -q --tb=short` 실행: **13 passed / 22.56s**, exit 0.
   - 생성 컨테이너 `solarops-quality-pg-9894acd49a`, `solarops-quality-s3-9894acd49a`.
   - PostgreSQL 실제 image ID: `sha256:38471f330eb885e04de130b768d6db4e10469e2311879c7e5c699f6d2d8a1c74`.
   - MinIO 실제 image ID: `sha256:ba58cd8f4781043abf8d5c3a3b656d4aba181dc5415ce7e884819b522a3b3955`.
   - 양 컨테이너 모두 probe 종료 뒤 별도 docker inspect에서 `exited` 확인. 컨테이너/데이터 삭제 없음. 자격증명/DSN은 출력하지 않음.
4. `scripts/demo/portfolio_demo.py --output artifacts/astra-r4-synthetic`
   - 7개 active, 재처리 hash 동일, 실패 보존 true, 보고서 생성 성공.
5. `scripts/release/release.py check`
   - `Release declarations aligned: 0.5.5`.
6. `artifacts/astra-r4-probe.py`
   - 평가용 새 합성 경로에서 보고서 키 충돌과 문서화된 인버터 소실 분모 변화를 확인.
   - 결과 `artifacts/astra-r4-probes/result.json`에 보존. 이 probe는 평가 산출물이며 프로젝트의 영구 회귀 스크립트로 추가한 것이 아님.

## 산출물

입력 사본 아래:

- `artifacts/astra-r4-pytest.xml` 및 최초 준비 오류 XML.
- `artifacts/astra-r4-pytest/` — 지정 pytest 임시 증거.
- `artifacts/astra-r4-services/services-fixed.xml`, `services-fixed-runtime.json`.
- `artifacts/astra-r4-synthetic/` — 7일 합성 raw/DB/보고서/실패 증거.
- `artifacts/astra-r4-probe.py`, `artifacts/astra-r4-probes/` — 일회 소형 재현 코드와 결과.

pytest/Python의 통상 cache 및 허용 서비스 driver가 기본 pytest tmp_path에 만든 새 합성 자료가 있을 수 있다. 기존 원본·raw·제품 서비스는 건드리지 않았다. shell에 출력된 명령 성공/요약과 위 machine-readable 결과를 함께 근거로 사용했다. 설치/빌드/전체 데이터/실제 스케줄/복원/부하/브라우저 검사를 직접 실행한 것으로 주장하지 않는다.
