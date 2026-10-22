# 개발과 검증

[프로젝트 홈](README.md) · [설치](docs/guides/setup.md) · [스크립트](scripts/README.md)

Python 3.12와 uv를 사용하며 모든 명령은 저장소 루트에서 실행합니다. Windows `.venv`와 WSL `.venv-linux`, 각 OS의 SQLite 파일은 분리합니다. WSL에서는 `make install lint test`를 사용할 수 있습니다.

```text
uv sync --frozen
uv run ruff check src tests scripts dags
uv run ruff format --check src tests scripts dags
node --check src/solarops/api/static/dashboard.js
uv run python scripts/validation/check_docs.py
uv run pytest -q
uv run python scripts/demo/portfolio_demo.py
uv build --wheel --out-dir artifacts/dist
```

Node는 JS 문법 검사에만 필요합니다. 오프라인 테스트와 합성 데모는 외부 데이터 다운로드를 하지 않습니다. PostgreSQL·MinIO 통합 검사는 Compose 실행 후 `uv run python scripts/validation/service-test.py`로 별도 수행합니다. 실행/재시도/KPO 검사는 [DAG 안내](docs/runbooks/dags.md)를 따릅니다.

## 변경 원칙

- 계산식·품질 규칙·분모·시간대 해석을 바꾸면 `CALCULATION_VERSION`과 회귀 fixture, 재처리 범위를 함께 검토합니다. API 오류 처리나 문서 정리는 계산 결과를 변경하지 않습니다.
- 원본 ZIP·raw 파일·기존 산출물·`docs/plan/`은 보존합니다. 고객/비밀 파일, `.env`, 로컬 데이터와 실행 로그를 커밋하지 않습니다.
- 동작 변경에는 실제 실패를 잡는 검사를 추가합니다. 문서만 바꿀 때 구현을 복제하는 단위 검사를 만들지 않습니다.
- 스크립트 위치를 변경하면 Makefile·CI·다른 스크립트·문서 명령을 함께 갱신합니다. Python 루트 경로와 셸 `cd`를 확인합니다.
- 검증 문서에는 실행한 환경·버전·명령·결과·제외 범위를 기록합니다. 과거 부하 측정을 현재 버전의 새 측정처럼 표현하지 않습니다.
- 의존성 변경은 `pyproject.toml`과 `uv.lock`을 함께 갱신합니다. 앱 버전 변경은 `src/solarops/__init__.py`, 이미지 태그·DAG·Helm·스크립트 참조도 맞춥니다.

## 소스 전달

```text
uv run python scripts/release/package_source.py
uv run python scripts/release/package_source.py --output artifacts/review-copy.zip
```

기본 ZIP 이름은 pyproject.toml 버전에서 생성합니다. Git 추적 파일과 무시되지 않은 새 파일을 포함하고 SHA-256 manifest를 추가합니다. 기존 ZIP은 덮어쓰지 않습니다. 강제로 추적된 `.env*`·데이터·런타임·키 파일 및 심볼릭 링크는 출력 생성 전에 거부합니다. 이 검사는 범용 비밀정보 탐지기가 아니므로 커밋 전 `git diff --cached`로 실제 포함 내용을 검토합니다.

CI는 Ubuntu/Windows에서 위 검사·일반 합성 데모·복구 데모·wheel·소스 패키징을 실행하고 7일간 합성 결과와 검사 증거를 보관합니다. 로컬 Compose/kind와 공개 전체 처리 결과는 CI 오프라인 통과만으로 대체하지 않습니다.
