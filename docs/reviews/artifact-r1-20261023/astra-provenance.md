# Astra R1 provenance

날짜: 2026-10-23 Asia/Seoul. 작업 디렉터리: `H:/dev/solarops_audit`.

- 모델: `gpt-6-astra`, reasoning effort `high`, `fork_turns=none`. 메인 세션이 실제 spawn 인수를 확인했다. 이름만으로 모델을 추정하지 않았다.
- 고정 검토 HEAD: `adc75001360a767f9d10ed4066d42a31a0b6abf0`.
- 구현: `39a56e768fc67b0011a77cb7c0cd31ef4b2155a0`, v0.5.2, energy-interval-v2.
- 사용 도구: `functions.exec` → `exec_command`(PowerShell), `apply_patch`(최종 두 파일 작성), 메인 세션과 `send_message`(모델 확인). 다른 평가자와 소통하지 않았다. 서브에이전트는 생성하지 않았다.
- 독립성: 과거 평가 원문/점수·다른 리뷰·plan 목표 점수·handoff를 읽지 않았다. README/quality/ADR에 기존 수정이나 평가 링크가 있다는 사실은 보았으나 그 링크의 평가 원문을 열지 않았다. 독립 산출물 평가이므로 진행 재개용 handoff/plan 순서를 적용하지 않았다.
- 제한: 서비스·실제 데이터는 건드리지 않았다. `.env`, 인증 파일, Secrets는 열지 않았다. 네트워크·다운로드·서비스 조작·전체 테스트는 실행하지 않았다.

## 읽기 경로

아래는 내용을 읽은 경로다. 단순 `rg --files`로 열거된 파일은 내용 검토로 계산하지 않았다.

전체 읽기:

```text
AGENTS.md
README.md
docs/reviews/portfolio-rubric.md
docs/benchmarks/quality-v0.5.2.md
docs/benchmarks/quality-v0.5.2.json
docs/benchmarks/stack-authenticity-20261023.md
docs/benchmarks/reliability-v0.4.0.md
docs/benchmarks/incremental-v0.5.0.md
docs/data-contract.md
docs/ons-source-contract.md
docs/architecture/system.md
docs/architecture/technology-stack.md
docs/adr/0008-storage-integrity.md
docs/runbooks/recovery.md
docs/runbooks/backup-restore.md
docs/portfolio/DEMO_GUIDE.md
docs/releases/0.5.2.json
pyproject.toml
.github/workflows/ci.yaml
src/solarops/contracts/brpvgen.py
src/solarops/normalize/parquet.py
src/solarops/pipeline.py
src/solarops/analytics/metrics.py
src/solarops/acquisition/ons.py
src/solarops/storage/minio.py
src/solarops/storage/postgres.py
src/solarops/config.py
src/solarops/reports/render.py
src/solarops/reports/freshness.py
src/solarops/api/app.py
src/solarops/api/readmodels.py
src/solarops/admin/app.py
src/solarops/runtime.py
src/solarops/diagnostics.py
scripts/demo/portfolio_demo.py
dags/solarops_factory.py
infra/docker/Dockerfile
infra/docker/Dockerfile.minio
tests/conftest.py
tests/test_contracts.py
tests/test_calculation_v2.py
tests/test_publication_boundaries.py
tests/test_integrity_boundaries.py
```

부분 읽기/검색:

```text
uv.lock — 처음 22줄: Python 범위 및 artifact hash 구조
tests/test_pipeline.py — 처음 100줄; 이후 선택 테스트 실행 시 모듈 import
docs/benchmarks/technical-20261023.json — 처음 75줄만
docs/benchmarks/evidence/stack-authenticity-20261023.json — 처음 95줄만
src/solarops/reports/templates/monthly.html — interpol|보간|알 수 없음 일치 줄
src/solarops/api/static/dashboard.js — 동일 문자열 일치 줄
src/solarops/cli.py — main/add_parser/ingest/build_report/replay/ons/host/Settings 일치 줄
tests/test_services.py — 테스트 이름/mark/postgresql 관련 일치 줄만
tests/test_admin.py — 테스트 이름/mark 관련 일치 줄만
tests/test_api_validation.py — 테스트 이름/mark 관련 일치 줄만
```

데모/선택 pytest 실행 시 패키지와 fixture 모듈을 import했다. 이는 관련 파일을 전부 정적 검토했다는 뜻은 아니다. `src/solarops/release.json`은 runtime 모듈의 로드와 생성된 보고서/실행 계보를 통해 확인했다. 첫 병렬 읽기 도구 결과가 총 출력 제한으로 일부 생략되어 pipeline/metrics 및 system 문서는 개별 명령으로 다시 읽었다.

## 실행한 읽기 명령

PowerShell `Get-Content`는 위 전체 읽기 목록을 묶어서 실행했다. 실행한 명령군은 다음과 같다(세미콜론은 독립 읽기를 묶은 실제 shell 구문).

```powershell
Get-Content README.md; Get-Content docs/reviews/portfolio-rubric.md; Get-Content docs/benchmarks/quality-v0.5.2.md
git rev-parse HEAD; git status --short; Get-Content AGENTS.md
rg --files src tests dags infra .github scripts/demo docs/architecture docs | Select-String -NotMatch 'reviews/|worklog/|plan/'
Get-Content docs/data-contract.md; Get-Content docs/ons-source-contract.md; Get-Content src/solarops/contracts/brpvgen.py; Get-Content src/solarops/normalize/parquet.py
Get-Content src/solarops/pipeline.py; Get-Content src/solarops/analytics/metrics.py
Get-Content docs/architecture/system.md; Get-Content docs/architecture/technology-stack.md; Get-Content docs/benchmarks/quality-v0.5.2.json; Get-Content docs/releases/0.5.2.json; Get-Content pyproject.toml; Get-Content .github/workflows/ci.yaml
Get-Content src/solarops/acquisition/ons.py
Get-Content src/solarops/storage/minio.py; Get-Content src/solarops/config.py; Get-Content src/solarops/reports/render.py; Get-Content src/solarops/reports/freshness.py
Get-Content src/solarops/storage/postgres.py
Get-Content src/solarops/api/app.py; Get-Content tests/test_contracts.py; Get-Content tests/test_calculation_v2.py
Get-Content tests/conftest.py; Get-Content tests/test_publication_boundaries.py; Get-Content tests/test_integrity_boundaries.py
Get-Content scripts/demo/portfolio_demo.py; Get-Content dags/solarops_factory.py; Get-Content infra/docker/Dockerfile; Get-Content infra/docker/Dockerfile.minio; Get-Content src/solarops/runtime.py; Get-Content src/solarops/diagnostics.py
Get-Content src/solarops/api/readmodels.py; Get-Content docs/runbooks/recovery.md; Get-Content docs/runbooks/backup-restore.md; Get-Content docs/benchmarks/reliability-v0.4.0.md; Get-Content docs/benchmarks/incremental-v0.5.0.md
Test-Path .venv/Scripts/python.exe
rg -n 'interpol|보간|알 수 없음' src/solarops/reports/templates/monthly.html src/solarops/api/static/dashboard.js
Get-Content tests/test_pipeline.py -TotalCount 100
Get-Content docs/benchmarks/stack-authenticity-20261023.md
Get-Content docs/benchmarks/technical-20261023.json -TotalCount 75
Get-Content src/solarops/admin/app.py
rg -n '^def test_|^@pytest.mark|PostgreSQL|postgresql' tests/test_services.py tests/test_admin.py tests/test_api_validation.py
Get-Content docs/architecture/system.md; Get-Content docs/portfolio/DEMO_GUIDE.md; Get-Content uv.lock -TotalCount 22
rg -n 'source_interpolation_ratio|interpolation_unknown_slots|if inv_rows|for offset|def upload|head_object|scope=|all-|if source_kind|snapshot\(' src/solarops/analytics/metrics.py src/solarops/pipeline.py src/solarops/storage/minio.py src/solarops/reports/render.py src/solarops/storage/postgres.py
rg -n 'def main|add_parser|ingest\(|build_report\(|replay\(|ons|host=|Settings' src/solarops/cli.py
rg -n '현재 앱|최신0|최신 릴리스' docs/architecture/system.md
Get-Content docs/adr/0008-storage-integrity.md
Get-Content docs/benchmarks/evidence/stack-authenticity-20261023.json -TotalCount 95
git status --short; git rev-parse HEAD
```

HEAD는 두 번 모두 고정 커밋과 일치했고 status는 두 번 모두 비어 있었다. 파일 열거의 경로 구분자 차이 때문에 배제 필터가 일부 리뷰/작업 로그 이름을 출력했으나 해당 파일 내용은 열지 않았다.

## 직접 실행한 작은 검사

모두 PowerShell의 single-quoted here-string을 `.venv/Scripts/python.exe -B -`에 전달했다. `-B`로 저장소 pycache 생성을 피하고, DuckDB 임시 파일은 각 새 temp root에 한정했다. 기존 파일을 삭제하거나 임시 경로를 정리하지 않았다. 실행 Python은 3.12.13이었다.

### 1. D1/D2 재현

입력 stdin 코드:

```python
import csv, json, os, sys, tempfile
from pathlib import Path
from solarops.config import Settings
from solarops.pipeline import ingest
from solarops.reports.render import build_report
from solarops.storage.postgres import Catalog
root=Path(tempfile.mkdtemp(prefix='solarops-astra-r1-'))
os.environ['SOLAROPS_DUCKDB_TEMP_DIR']=str(root/'duckdb-temp')
s=Settings(root=root/'store',database_url='sqlite:///'+(root/'catalog.db').as_posix(),s3_endpoint=None,org='demo',timezone='UTC',source_root=root/'input',environment='native')
p=root/'input'; p.mkdir()
meta=p/'metadata.csv'; meta.write_text('id,nominal_power_mw\nDEMO_01,0.02\n',encoding='utf-8')
inv=p/'inverter.csv'; station=p/'station.csv'; station.write_text('datetime,ps_id,poa_irradiance_wm2\n',encoding='utf-8')
def source(days):
    with inv.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['datetime','ps_id','inverter_id','total_active_power_w','interpolated_keys_total_active_power_w','document_count_total_active_power_w'])
        for day in days: w.writerow([f'2024-04-{day:02d}T12:00:00Z','DEMO_01','1','1000','','3'])
def run(v): return ingest(s,meta,inv,station,'DEMO_01','2024-04-01','2024-04-03',v)
source([1,2]); a=run('v1')
report=build_report(s,'2024-04','DEMO_01','synthetic')
r=json.loads((Path(report['local_directory'])/'manifest.json').read_text(encoding='utf-8'))
html=(Path(report['local_directory'])/'report.html').read_text(encoding='utf-8')
print(json.dumps({'probe':'unknown_interpolation','observed':sum(m['observed_slots'] for m in r['metrics']),'unknown':sum(m['interpolation_unknown_slots'] for m in r['metrics']),'report_interpolation':r['interpolation'],'html_zero_percent':'<dt>원본 보간 표시</dt><dd>0.00%' in html},ensure_ascii=False))
source([1]); b=run('v2')
c=Catalog(s,read_only=True); snap=c.snapshot('demo')
print(json.dumps({'probe':'shrinking_source_bounds','first_published_days':[x['day'] for x in a['results']],'corrected_published_days':[x['day'] for x in b['results']],'active':[{'day':x['partition_id'],'version':x['payload']['active_source_version'],'energy':x['metric']['estimated_energy_kwh']} for x in snap]},ensure_ascii=False)); c.engine.dispose()
print(json.dumps({'python':sys.version.split()[0],'isolated_root':str(root),'source_rows_max':2,'network':False,'production_services':False},ensure_ascii=False))
```

exit 0. 결과:

```json
{"probe":"unknown_interpolation","observed":2,"unknown":2,"report_interpolation":0.0,"html_zero_percent":true}
{"probe":"shrinking_source_bounds","first_published_days":["2024-04-01","2024-04-02"],"corrected_published_days":["2024-04-01"],"active":[{"day":"2024-04-01","version":"v2","energy":0.25},{"day":"2024-04-02","version":"v1","energy":0.25}]}
```

새 경로: `C:/Users/Taeyang/AppData/Local/Temp/solarops-astra-r1-5bhzos20`.

### 2. 기존 오프라인 데모

입력 stdin 코드:

```python
import os, runpy, sys, tempfile
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='solarops-astra-demo-r1-'))
os.environ['SOLAROPS_DUCKDB_TEMP_DIR']=str(root/'duckdb-temp')
sys.argv=['scripts/demo/portfolio_demo.py','--output',str(root/'demo')]
runpy.run_path('scripts/demo/portfolio_demo.py',run_name='__main__')
```

exit 0. failed_publish_kept_active_data=true, replay_hashes_identical=true, active_partitions=7, committed batch=2, failed batch=1. 생성 report ID `d876cde1-691e-4a3e-9e7d-fa1eb308d29e`, partial_period. 서버 옵션은 사용하지 않았다.

새 경로: `C:/Users/Taeyang/AppData/Local/Temp/solarops-astra-demo-r1-k696xupy/demo`. 이 경로의 `evidence.json`에 7개 일별 hash와 보고서 artifact hash가 있다. 생성된 값은 이번 세션에서 실행한 합성 결과이며 기존 공개 데이터의 결과가 아니다.

### 3. 기존 선택 회귀

입력 stdin 코드:

```python
import os, sys, tempfile
from pathlib import Path
import pytest
root=Path(tempfile.mkdtemp(prefix='solarops-astra-pytest-r1-'))
os.environ['SOLAROPS_DUCKDB_TEMP_DIR']=str(root/'duckdb-temp')
os.environ['SOLAROPS_ORG']='demo'
os.environ['SOLAROPS_REPORT_TIMEZONE']='UTC'
print('isolated_root='+str(root))
sys.exit(pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(root/'cases'),'tests/test_contracts.py::test_golden_energy_duplicates_and_missing','tests/test_pipeline.py::test_failure_keeps_published_partition','tests/test_publication_boundaries.py::test_ons_incremental_correction_withdrawal_and_atomic_cursor']))
```

exit 0, **4 passed in 2.70s**. before/during commit의 parameter 2개를 포함한다. 기존 pytest cache를 쓰지 않았고 새 basetemp를 명시했다. HTTP TestClient는 격리 앱의 in-process 요청이며 실제 서비스가 아니다.

새 경로: `C:/Users/Taeyang/AppData/Local/Temp/solarops-astra-pytest-r1-f148_gbk`.

## 쓰기 범위와 미실행

저장소에 작성한 것은 UTF-8 최종 평가 원문 `artifacts/artifact-review-r1-20261023/astra-review.md`와 이 provenance 두 파일뿐이다. 허용된 비파괴 검사 데이터는 위 세 새 OS 임시 경로 안에 있다. 코드·문서·기존 산출물·raw 데이터는 수정하지 않았다.

전체 pytest, 서비스 13검사, CI 원격 상태, Kubernetes/Airflow 실제 실행, 새 venv/OS 설치, 공개자료 해시/재처리, 브라우저/접근성 검사는 이번에 실행하지 않았다. 보존 문서의 결과를 독립 재실행으로 표기하지 않았다. 원본 테스트 로그나 공개 raw를 읽지 않았으므로 보존 JSON의 주장도 그 범위에서만 사용했다.

작성 후 추가 확인: `.venv/Scripts/python.exe -B -`에서 두 파일을 `read_bytes().decode('utf-8')`로 읽고 평가 표의 점수를 정규식으로 합산했다. UTF-8 디코딩 성공, 항목 20개, 합계 86을 확인했다. 이 검사는 파일을 수정하지 않았다.
