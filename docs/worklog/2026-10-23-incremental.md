# 2026-10-23 — 갱신 원천과 제한 병렬 처리

## 착수 판단

- DATA-03(19점)을 먼저 진행합니다. ONS 공식 월별 CSV·CKAN metadata·데이터 사전(2023-06-09)을 확인했습니다. 2026-10 파일은 47,357,126바이트, 전체365,040행 중 태양광69,696행입니다.
- `val_geracao`는 MWmed이며 datetime의 시간대·구간 시작/끝은 사전에 없습니다. 원문 시각을 보존하고 UTC·kWh·BR-PVGen 지표로 변환하지 않습니다. Type III 예측·MMGD 미확정·일반 verified를 구분합니다.
- 월별 성공 cursor와 일별 내용 hash를 사용합니다. 현재/이전 월을 매일 재확인하며 두 달보다 오래된 정정은 명시적 월 지정으로 수집합니다. 원본과 metadata는 immutable raw로 보존합니다.
- PERF-03(14점)은 실제 Airflow KPO로 공개 PS_001의 4일을 직렬/동시2에서 처리합니다. 결과 hash 동일·오류0·각 worker RSS<2GiB·10분 이내 완료를 로컬 수용 기준으로 삼고, 동시2의 wall time 15% 이상 감소 시에만 병렬 사용을 권합니다. 단일 kind 호스트 실험이며 운영 SLO가 아닙니다.
- PDF 스킬은 공식 사전 텍스트 확인에 사용했습니다. 상세 원본·HTTP 증거는 Git 제외 `artifacts/incremental-20261023/`에 보존합니다. 원본·기존 게시 데이터의 삭제는 하지 않습니다.

## 구현과 데이터 무결성

- 출처별 `acquisition/ons.py`, `ons-sync`/`ons-status`, 별도 읽기 API와 조직별 collection 테이블3개를 추가했습니다. [입력·유형·철회·실패 계약](../ons-source-contract.md)에 원문 시각/MWmed와 라이선스 버전 미명시를 기록했습니다.
- 성공 cursor와 변경 날짜를 같은 transaction으로 전환하고 오래된 동시 실행은 CAS 충돌로 거부합니다. 같은 응답은 재분석하지 않으며 원본·metadata·미게시 객체를 보존합니다.
- 기존 계약/게시/서비스 검사에 영향이 큰 데이터 경계만 보강했습니다. `uv run pytest -q` 136통과·14제외, 격리 PostgreSQL/MinIO 13통과. 실제 전체 자료는 offline test에서 다운로드하지 않습니다.
- 구현 `f4f3334` 이후 실제 Airflow DagBag에서 새 파일의 safe-mode 탐색 누락을 발견했습니다. docstring을 고친 `853de23` 이미지에서 local/Kubernetes 모드 각각7DAG import·템플릿 검사 성공을 확인했습니다.

## 실제 배포·수집

- 릴리스0.5.0 선언·lock 정렬 → 구현 커밋 → `scripts/release/release.py build` → Compose `db-migrate`/dashboard 교체 → `scripts/ops/k8s-refresh.sh` 순서로 반영했습니다. [Git/image ID](../releases/0.5.0.json)를 보존합니다.
- Compose `ons-sync --period 2026-10` 최초21일·69,696태양광행 게시, 같은월 재실행 변경0개. `/health`·`/ready`·ONS status/day 정상이며 기존 공개 API3응답은 전후 바이트 동일합니다.
- kind ONS를 unpause해 실제 `scheduled__2026-10-23T05:00:00+00:00`가 성공했습니다. 9~10월167,424태양광행·51일 게시, Compose와10월 논리hash 전부 일치. [수집 수치·확인 범위](../benchmarks/incremental-v0.5.0.md).
- ONS만 매일14:00KST 활성, 다음10-24 14시입니다. 나머지6DAG paused·진행/대기0건. Compose Airflow3개는0.5.0으로 생성 후 중지 상태를 유지했습니다. [일정 on/off](../runbooks/dags.md#ons-정기-수집-켜기끄기).

## 실제 DAG 성능과 판단

- 기존 `scripts/validation/k8s_benchmark.py`를 실제 Airflow 공개4일 KPO 비교로 교체했습니다. 매 시행 새 DB/버킷·작업 경로를 만들어 기존 demo 공개 결과를 보존합니다.
- 직렬36.675초→동시2개19.339초,14,976행·4일hash동일·8task성공. 실제 Pod 구간으로 동시1/2도 확인했습니다. 최대workerRSS427.78MiB, 총CPU16.470→20.468초입니다.
- 시간47.3%단축으로 착수 기준을 충족하지만 CPU24.3%증가·공유단일호스트·직렬후병렬각1회·파일캐시 한계가 있습니다. 이 독립task 유형에2개까지만 권고하며 기본 수집은1개를 유지합니다.
- DB·S3·서비스 자원 표본, 조건과 미검증 범위는 [측정 문서](../benchmarks/incremental-v0.5.0.md)에 모았습니다. 단일CLI4일배치와의 비교나 다중물리노드 성능이라고 주장하지 않습니다. 시험 자원은 종료/paused 후 데이터와 증거를 보존했습니다.

## 문서와 GitHub 전달

- README·출처·수집/운영 안내·아키텍처·현재 구현 상태·변경 이력·스킬 목적을 최신화했습니다. DATA-03/PERF-03을 미완료 plan에서 제거했고 handoff는100줄·최근8개 이내로 유지했습니다. 영업은 계속 후순위입니다.
- 비공개 저장소임을 다시 확인하고 구현 `853de23`을 push했습니다. [CI39910321487](https://github.com/TaeyanG4/solarops-audit/actions/runs/39910321487)는 Ubuntu/Windows 각각137통과·13제외, 릴리스 선언·합성 데모·복원·wheel/소스 패키징까지 성공했습니다.
- 로컬의 추가 제외1건은 호스트에서 시험용 symlink를 만들 수 없어 제외한 경로이탈 검사입니다. CI에서는 실행·통과했습니다. 서비스13검사는 별도 실제 PostgreSQL/MinIO 근거이며 offline CI 통과에 합산하지 않습니다. 원본·비밀키·데이터셋은 커밋하지 않았습니다.
