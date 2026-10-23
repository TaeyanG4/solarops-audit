# Astra R2 평가 provenance

- 평가 일자: 2026-10-23, Asia/Seoul. 직접 합성 데모 보고서 시각 `2026-10-23T08:48:29.627639+00:00`; 진단 probe 시각 `2026-10-23T08:51:36+00:00`.
- 태스크 생성 설정: **gpt-6-astra / high / fork_turns=none**, 독립 `/root/astra_artifact_r2` 세션. 이전 평가 내용·점수·목표 점수·타 평가자의 결과를 제공받거나 읽지 않았다. 다른 에이전트와 메시지를 주고받지 않았다.
- 저장소: `H:/dev/solarops_audit`. 시작/마지막 확인 HEAD `dbfb04ca4a3a9bf7c0f9e2b7de552079b2312cf5`. 릴리스 기록의 구현 커밋 `038a000b69befaa77efd918a0b9654ba866ce501`, 앱 0.5.3 / energy-interval-v2.
- 기존 미커밋 상태: `skills-lock.json` 수정, `.taste-skill/`, `landing/` untracked. 읽기·실행·평가 대상에서 제외했다. `git diff --name-only <평가 SHA> -- src tests scripts dags infra pyproject.toml uv.lock README.md docs`는 출력 없음. 평가에 사용한 코드/문서는 고정 커밋과 같았다.
- 준수한 경계: AGENTS.md의 안전·원본 보존, 사용자 지정 블라인드 평가 예외. handoff.md·plan.md·과거 docs/reviews(고정 rubric 제외)·docs/worklog(허용한 bounds-reproduction 제외)·artifacts의 기존 평가 결과를 읽지 않았다. 허용된 README/벤치마크에 들어 있는 과거 평가 링크·수정 배경 문구는 보였지만 그 링크를 열거나 점수를 보지 않았다.
- 도구: `functions.exec`를 통한 `exec_command`(PowerShell), `write_stdin`, 마지막 두 결과 파일의 `apply_patch`. Python 3.12.13 / uv 0.11.29. 네트워크·브라우저·서비스 관리 도구를 사용하지 않았다. 특수 스킬은 적용하지 않았다.

## 직접 검토한 범위

중심 문서: AGENTS.md; README.md; 고정 `docs/reviews/portfolio-rubric.md`(git show); pyproject.toml; uv.lock의 헤더/해시 예; docs/data-contract.md; docs/ons-source-contract.md; docs/architecture/system.md의 환경/게시 구조 부분과 docs/architecture/technology-stack.md; docs/adr/0008-storage-integrity.md; docs/runbooks/recovery.md 및 backup-restore.md; docs/portfolio/DEMO_GUIDE.md; docs/guides/setup.md; docs/IMPLEMENTATION_STATUS.md.

최신/역사 근거: docs/benchmarks/quality-v0.5.3.md/json; quality-v0.5.2.json; integrity-v0.4.2.md; reliability-v0.4.0.md; stack-authenticity-20261023.md; incremental-v0.5.0.md/json; 허용된 docs/worklog/2026-10-23-bounds-reproduction.md; docs/releases/0.5.3.json. 원격 CI 링크나 기록이 가리킨 원본 로그는 추가 조회하지 않았다. 큰 묶음 출력이 일부 잘린 경우 핵심 파일은 별도 재조회했고, 모든 저장소 파일을 완독했다는 주장은 하지 않는다.

코드: src/solarops/contracts/brpvgen.py; normalize/parquet.py; analytics/metrics.py; pipeline.py; acquisition/ons.py 및 brpvgen.py; storage/postgres.py 및 minio.py; config.py; reports/render.py 및 freshness.py; api/app.py 및 readmodels.py; diagnostics.py; cli.py; replay.py; runtime.py; release.json; admin/app.py. dashboard.js의 상태 초기화·보간 표시 함수 및 관련 검색 결과, fixtures.py의 생성 함수 위치도 확인했다. admin/services.py 구현 전체와 CSS/HTML 전체는 검토하지 않았다.

배포/시연/검사: dags/solarops_factory.py; infra/docker/Dockerfile 및 Dockerfile.minio; airflow-constraints-3.12.txt의 버전 목록 예와 hash 강제 유무 검색; migrations/0001_catalog.sql; .github/workflows/ci.yaml 및 services.yaml; scripts/demo/portfolio_demo.py; tests/conftest.py; tests 전체의 검사 이름 목록; 실제 실행한 5개 검사 파일 중 pipeline/calculation/publication/integrity 본문과 contracts의 주요 계약/검사 이름. `release.py check`는 기존 도구를 그대로 실행했다. .env·실제 인증정보·Secret·고객 자료를 읽지 않았다.

## 실제 명령과 결과

저장소 루트 PowerShell에서 수행했다. 명령은 독립 도구 호출로 실행했고 여기에는 핵심 검증을 보존한다.

```powershell
git rev-parse HEAD
git status --short
git show dbfb04ca4a3a9bf7c0f9e2b7de552079b2312cf5:docs/reviews/portfolio-rubric.md
.venv\Scripts\python.exe --version
uv --version
.venv\Scripts\python.exe -m pytest -q tests/test_contracts.py tests/test_pipeline.py tests/test_calculation_v2.py tests/test_publication_boundaries.py tests/test_integrity_boundaries.py -p no:cacheprovider
.venv\Scripts\python.exe scripts/demo/portfolio_demo.py --output artifacts/astra-r2-synthetic-20261023
.venv\Scripts\python.exe scripts/release/release.py check
git diff --name-only dbfb04ca4a3a9bf7c0f9e2b7de552079b2312cf5 -- src tests scripts dags infra pyproject.toml uv.lock README.md docs
git status --short
git rev-parse HEAD
```

결과: pytest **79 passed in 26.91s**, exit 0. 데모 exit 0, active 7, 실패 보존 true, replay hash 일치 true, committed 2 / failed 1. release check `Release declarations aligned: 0.5.3`, exit 0. 시작·종료 HEAD 일치, 대상 tracked diff 없음. 테스트는 기존 `conftest.py`가 생성한 새 UUID의 `artifacts/test-tmp/` 하위 합성 파일/SQLite만 사용했다. 기존 파일에 대한 삭제나 cleanup 명령은 실행하지 않았다. 테스트 함수 안의 고장 주입은 해당 새 fixture에만 적용됐다.

F1의 추가 검사는 영구 스크립트 없이 아래 Python을 PowerShell here-string으로 `.venv\Scripts\python.exe -`에 전달했다. 한 번 실행했으며 폴더를 보존했다. 비수치 synthetic 값 자체는 비밀이 아니다.

```python
import csv, json
from pathlib import Path
from solarops.config import Settings
from solarops.fixtures import generate
from solarops.pipeline import ingest
from solarops.storage.postgres import Catalog, runs
from sqlalchemy import select
root=Path('artifacts/astra-r2-diagnostic-20261023').resolve()
root.mkdir(exist_ok=False)
paths=generate(root/'input')
with paths['inverter'].open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
rows[2]['total_active_power_w']='synthetic-nonnumeric'
with paths['inverter'].open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
s=Settings(root=root/'data',database_url='sqlite:///'+(root/'catalog.db').as_posix(),
           s3_endpoint=None,org='demo',timezone='UTC')
try:
    ingest(s,paths['metadata'],paths['inverter'],paths['station'],
           'DEMO_01','2024-04-01','2024-04-02','diagnostic-v1')
except ValueError as exc:
    print('exception_type='+type(exc).__name__)
c=Catalog(s,read_only=True)
with c.engine.connect() as conn:
    result=[{'status':r['status'],'payload':r['payload']}
            for r in conn.execute(select(runs)).mappings()]
print(json.dumps({'runs':result,'active_count':len(c.snapshot('demo')),
                 'quarantine_count':len(list(s.root.rglob('quarantine.json')))},
                 ensure_ascii=False,indent=2))
```

결과는 ValueError, failed batch 하나, stage processing_partitions, error_code BR_INPUT_INVALID, active_count 0, quarantine_count 0이었다. 공개 입력의 결함 빈도나 전체 자료 영향을 추정하지 않았다. 기존 게시 데이터가 잘못 바뀌었다는 결과도 아니다.

## 실행하지 않은 것과 산출물

기존 venv를 이용했으며 새 clone/uv sync/패키지 다운로드·설치·전체 데이터 다운로드를 수행하지 않았다. 실제 PostgreSQL/MinIO/Airflow/Kubernetes·외부 CI·브라우저는 건드리지 않았고 검증하지 않았다. 서비스 성공·배포·공개 전체 처리·독립 CSV 산술·양 OS CI는 문서 및 기계 판독 기록의 역사 증거로만 사용했다. constraints 무해시 설치는 정적 재현 제한이며 캐시 없는 빌드 실패를 재현한 것이 아니다.

추가 생성물: 이 디렉터리의 `astra-review.md`, `astra-provenance.md`(UTF-8), 새 `artifacts/astra-r2-synthetic-20261023/`, 새 `artifacts/astra-r2-diagnostic-20261023/`, pytest의 새 UUID 임시 경로와 일반 Python bytecode cache. 코드·문서·기존 원본·기존 평가를 변경하지 않았다. handoff/plan/worklog 갱신은 블라인드 읽기 전용 평가 범위에서 수행하지 않았다.
