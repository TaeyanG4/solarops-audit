# 2026-10-23 — 범위 계산 측정 재현

[v0.5.2 결과](../benchmarks/quality-v0.5.2.md) · [v0.5.3 결과](../benchmarks/quality-v0.5.3.md)

과거 SQL 범위 함수와 현재 검증 함수만 비교합니다. 보존 PS_001 인버터 CSV(138,848,090바이트), Git 이력, Python3.12/uv 환경이 필요합니다. 아래를 `uv run python`으로 실행하며 파일 경로만 맞춥니다. 다운로드·DB·원본 수정은 하지 않습니다. 출처 불명 커밋으로 baseline을 교체하지 않습니다.

```python
import ast, json, subprocess, time
from datetime import UTC
from pathlib import Path
import duckdb
from solarops.normalize.parquet import configure_duckdb, inverter_id, sql_quote
from solarops.pipeline import canonical_hash, source_bounds

old_source=subprocess.check_output(['git','show','548ce66:src/solarops/pipeline.py'],text=True)
node=next(n for n in ast.parse(old_source).body if isinstance(n,ast.FunctionDef) and n.name=='source_bounds')
namespace={'UTC':UTC,'duckdb':duckdb,'configure_duckdb':configure_duckdb,'inverter_id':inverter_id,'sql_quote':sql_quote}
exec(compile(ast.Module(body=[node],type_ignores=[]),'<historical-source-bounds>','exec'),namespace)
path=Path('data/source/inverter/BR-PVGen_inverter/PS_001.csv')
trials=[]
for i in range(3):
    order=('baseline','current') if i%2==0 else ('current','baseline')
    for label in order:
        fn=namespace['source_bounds'] if label=='baseline' else source_bounds
        start=time.perf_counter();bounds=fn(path,'PS_001',{'PS_001'});elapsed=time.perf_counter()-start
        digest=canonical_hash({str(k):[v.isoformat() for v in value] for k,value in bounds.items()})
        trials.append({'iteration':i,'version':label,'seconds':elapsed,'inverters':len(bounds),'bounds_sha256':digest})
assert len({r['bounds_sha256'] for r in trials})==1
print(json.dumps(trials,indent=2))

```

v0.5.3 실행은 SQL 중앙값0.674초, 새 검증3.527초, 41개 인버터 min/max hash 동일입니다. v0.5.2 당시에는0.788→2.209초였습니다. 세 번씩 순서를 번갈았지만 단일 호스트·캐시·동시 호스트 작업 영향을 배제하지 못합니다. 현재 버전에서 실행하면 현재 파서를 측정하므로 과거0.5.2 수치의 재생은 아닙니다.

새 비용에는 전체 행의 Python 파싱과 허용 형식 검증이 포함됩니다. 전체 ingest·에너지 계산·KPO 성능 측정이 아닙니다. 원본이 없는 checkout은 이 검사를 생략하고 작은 합성 데모/오프라인 검사를 사용합니다. 상시 회귀 스크립트 대신 수동 재현 코드를 보존했습니다.
