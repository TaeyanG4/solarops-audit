# Astra 독립 평가 provenance

날짜: 2026-10-23 Asia/Seoul. 최종 평가 총점 96/100. [평가 원문](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/astra-review.md).

## 평가 식별과 경계

- 독립 task: `/root/astra_artifact_r5`. 부모가 생성 요청에 사용한 모델은 `gpt-6-astra`, reasoning_effort `high`, fork_turns `none`이라고 확인했다. 서버 측 실제 resolved model 식별자는 도구가 반환하지 않았으므로 그 이상은 주장하지 않는다.
- 유일한 검토 source root: `H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra`.
- 대상 commit: `faa6f3baf8e1925ccc21f402419cf1333f2e5010`; 앱 0.5.6; 구현 commit: `4b9959e232eccfcae1581c93d00bf3509c56549f`.
- REVIEW_SNAPSHOT.json 선언: tracked_file_count=303, archive SHA256=`81029212ac9dfd5bf657c12b68b964f73c20bd37b7efff9ca3e1c223e65d74b6`. 평가자는 archive 파일을 읽거나 그 전체 SHA를 독립 재계산하지 않았다. export metadata를 확인한 범위이다.
- 고정 평가표는 export의 `docs/reviews/portfolio-rubric.md`만 읽었다. 다른 평가·이전 점수·요구 점수·상대 평가는 찾거나 읽지 않았다. 원본 저장소·다른 evaluator export·parent artifacts를 탐색하지 않았다.
- handoff/plan/다른 reviews/작업일지/옛 계획/skills/landing 제외는 blind 지시로 존중했고 누락 결함으로 취급하지 않았다. 현재 README·상태/벤치마크 문서가 다른 평가를 언급하거나 링크하는 부분은 보였으나 링크를 따라가지 않았다.
- 외부읽기 예외: 승인된 `H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/service-probe.py`를 읽고 그대로 실행했다. Python bootstrap은 승인된 기존 Python3.12 실행파일을 사용했으며 원본 venv의 소스를 import하지 않았다.
- 기존 소스 파일을 수정하지 않았다. 새 .venv와 `source-astra/artifacts/`에만 실행 환경·합성 입력·검사 산출물을 만들었다. 이 provenance와 review 두 파일은 명시 허용된 상위 출력 위치에 작성했다.

## 도구·환경

도구: functions.exec → PowerShell exec_command / apply_patch, 부모에게 모델 요청 metadata 확인용 collaboration.send_message. 별도 agent를 생성하지 않았고 브라우저·원격 CI·외부 데이터 서비스는 사용하지 않았다.

Windows의 기존 CPython3.12.13으로 export에 새 `.venv`를 만들었다. 오프라인 uv sync는 pyarrow26.0.0 wheel 캐시 부재로 실패했다. 승인된 fallback인 `uv sync --frozen --python H:/dev/solarops_audit/.venv/Scripts/python.exe`로 locked 패키지 42개를 설치했다. 새 환경은 같은 OS·기존 인터프리터/uv/공유 package cache를 사용한 것이며 새 OS나 완전 무네트워크 설치는 아니다. 이후 제품 검사는 공개 데이터 네트워크 다운로드 없이 실행했다.

Python 실행 환경:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
$env:SOLAROPS_BUILD_REVISION='faa6f3baf8e1925ccc21f402419cf1333f2e5010'
```

`sys.version`: 3.12.13 (main, Jun 23 2026, 15:23:43) [MSC v.1944 64 bit (AMD64)]. `solarops.__file__`: `H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/src/solarops/__init__.py`.

## 읽은 범위

모든 아래 경로는 위 source root 안이다. 파일 전체를 출력한 경우와 일부 검색/절을 읽은 경우를 구분한다. 출력이 잘린 일부 대형 묶음은 전체를 읽었다고 주장하지 않는다.

- 규칙/진입: AGENTS.md, REVIEW_SNAPSHOT.json, docs/reviews/portfolio-rubric.md, README.md, pyproject.toml. uv.lock은 frozen 설치가 소비했으며 모든 lock 항목을 수동 검토하지 않았다.
- 계약·설계: docs/data-contract.md, docs/ons-source-contract.md, docs/architecture/technology-stack.md, docs/adr/0001–0008. docs/architecture/system.md는 주요 책임·거래·조회·운영·제약 절과 검색 행을 검토했다.
- 전달·운영: docs/portfolio/SUBMISSION.md, CASE_STUDY.md, docs/runbooks/recovery.md, backup-restore.md. docs/IMPLEMENTATION_STATUS.md 및 runbooks/dags.md는 현재 상태·재현·CLI·KPO 관련 절을 읽었다. DEMO_GUIDE.md는 목차/관련 범위 검색만 했다.
- 역사 증거: docs/benchmarks/quality-v0.5.6.md, technical-20261023.md, stack-authenticity-20261023.md, incremental-v0.5.0.md, evidence/technical-20261023/README.md와 provenance.json. latency-samples.json은 Python으로 전체 27조건/1,080표본을 재계산했다. docs/releases/0.5.6.json과 src/solarops/release.json을 대조했다. 링크된 다른 평가 및 작업일지는 읽지 않았다.
- 핵심 코드 전체: src/solarops/pipeline.py, analytics/metrics.py, normalize/parquet.py, contracts/brpvgen.py, config.py, storage/minio.py, storage/postgres.py, acquisition/ons.py, reports/render.py, reports/identity.py, reports/freshness.py, api/app.py, api/readmodels.py, diagnostics.py, replay.py, runtime.py, cli.py, admin/app.py.
- 실행/인프라: dags/solarops_factory.py, infra/docker/Dockerfile, Dockerfile.minio, .github/workflows/ci.yaml. Compose 설정과 admin/services.py는 관련 설정·경계 검색/일부를 검토했다. 실제 앱 infra에 apply/rollout/restart를 하지 않았다.
- 검사: tests/test_contracts.py, test_calculation_v2.py, test_services.py, conftest.py 전체를 읽었다. test_pipeline.py, test_publication_boundaries.py, test_integrity_boundaries.py, test_workspace.py, test_replay.py, test_diagnostics.py는 테스트 이름/위치·해당 계약을 확인했다. 전체 tests suite는 실행했지만 모든 테스트 함수를 줄별로 수동 감사하지 않았다. 데모/복원/release 스크립트는 실행 결과와 진입 함수를 확인했다.
- UI CSS/JS와 이미지에 대한 새로운 브라우저/시각 감사는 하지 않았다. 그 부분은 기존 문서 증거 및 이번 API/패키징 테스트 실행 범위에 한정한다.

## 정확한 실행과 산출물

작업 디렉터리는 source root. 각 넓은 검사는 한 번만 실행했다. 기존 소스/테스트에 영구 회귀 검사나 수정 코드를 추가하지 않았다.

```powershell
uv sync --frozen --offline --python H:/dev/solarops_audit/.venv/Scripts/python.exe
# cache miss → 실패
uv sync --frozen --python H:/dev/solarops_audit/.venv/Scripts/python.exe
# 성공
.venv/Scripts/python.exe -c "import sys,solarops; print(sys.version); print(solarops.__file__)"
.venv/Scripts/python.exe -m pytest -q --tb=short --junitxml=artifacts/astra-tests.xml -o cache_dir=artifacts/pytest-cache --basetemp=artifacts/pytest-tmp
.venv/Scripts/python.exe scripts/demo/portfolio_demo.py --output artifacts/astra-demo
.venv/Scripts/python.exe scripts/validation/backup_restore_drill.py --output artifacts/astra-restore
.venv/Scripts/python.exe scripts/release/release.py check
$env:PYTEST_ADDOPTS='-o cache_dir=artifacts/services-cache --basetemp=artifacts/services-tmp'
.venv/Scripts/python.exe H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/service-probe.py artifacts/astra-services
.venv/Scripts/python.exe artifacts/astra-focused.py
.venv/Scripts/ruff.exe check src tests scripts dags --no-cache
.venv/Scripts/ruff.exe format --check src tests scripts dags --no-cache
docker inspect --format '{{.Name}} {{.State.Status}} {{.Image}}' solarops-quality-pg-fd882f18ef solarops-quality-s3-fd882f18ef
```

PowerShell의 서로 다른 exec 호출 환경은 독립이므로 필요한 PYTHONPATH/PYTHONDONTWRITEBYTECODE/BUILD_REVISION을 각 Python 실행 호출에 다시 설정했다. PYTEST_ADDOPTS는 서비스 호출의 process에만 적용했다.

- [전체 검사 XML](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-tests.xml): 140 passed, 14 skipped, 43.21s. 제외된 정확한 이름/사유는 focused evidence에 추출해 보존했다. 13개 선택형 서비스 검사와 `test_source_symlink_cannot_escape_root`(Host does not permit test symlinks) 1개다.
- [서비스 검사 XML](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-services/services-fixed.xml): 13 passed, 29.18s. 일반 suite에서 제외된 서비스 검사를 실제 PostgreSQL/MinIO로 실행한 것이며 새로운 13개 기능을 추가한 것은 아니다.
- [격리 서비스 기록](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-services/services-fixed-runtime.json): exit_code0, isolated=true, stopped=true, deleted=false. docker inspect로 두 컨테이너 모두 exited 확인. PostgreSQL image ID `sha256:38471f330eb885e04de130b768d6db4e10469e2311879c7e5c699f6d2d8a1c74`, MinIO image ID `sha256:ba58cd8f4781043abf8d5c3a3b656d4aba181dc5415ce7e884819b522a3b3955`. 사전 존재한 pinned 이미지로 새 컨테이너를 만들었으며 이미지 재빌드는 하지 않았다. 무작위 포트·비밀을 사용했고 비밀값은 출력하지 않았다.
- [데모 evidence](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-demo/evidence.json): 7파티션, 실패 게시 보존, 재처리 동일 해시. 새 보고서 ID `f7f07fde-ba8c-4a6a-b4b0-9afa5803a104`, partial_period(7일/4월), HTML/CSV/manifest SHA 기록.
- [복원 evidence](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-restore/evidence.json): 정지 생산자 SQLite+로컬파일, 같은 호스트의 별도 경로. 34파일·7파티션, checksum·손상 거부·API·기존 보고서·raw replay·원본 비변경 true. 이번 PostgreSQL/MinIO 검사는 publication 시험이며 서비스 backup/restore를 새로 실행한 것으로 쓰지 않는다.
- [focused 임시 코드](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-focused.py), [evidence](H:/dev/solarops_audit/artifacts/artifact-review-r5-20261023/source-astra/artifacts/astra-focused/evidence.json): 두 조직의 동일 해시 확인 및 역사 latency 표본 계산. 별도 DB 두 개를 사용한 해시 재현 자체는 공유 DB 조직격리 증명이 아니다. 조직 격리는 기존 관련 suite 통과와 코드의 org 필터를 근거로 평가했다.
- Ruff check 성공 / format check 77파일 성공. release declarations aligned0.5.6. 실행 로그는 이 task의 도구 결과에도 남는다.

## 미실행·불확실성

공개 전체 BR 다운로드/재처리, ONS 외부 HTTP 수집, Airflow/kind 새 실행·Pod 장애·롤아웃, 서비스 restore drill, 브라우저 접근성, GitHub CI 재조회, wheel 독립 재설치, 타 OS/타 호스트, 장기 동시 쓰기·부하는 새로 실행하지 않았다. 과거 실행 기록을 읽은 것과 이번 직접 검사 결과를 분리했다. 원본 archive SHA를 독립 검증하거나 커밋 자체를 git object로 확인한 것도 아니다.

현재 로컬 범위에서 중요한 실행 검사 실패는 없었다. F1 문구 불일치는 합성 입력으로 확인했고, L1은 정적 비용 경계/L2는 증거 재생 범위의 한계이다. 이 세 사항을 동일 심각도의 기능 결함으로 묶지 않았다. 평가 원문 점수는 부모의 후속 수용 판단과 별개로 보존한다.
