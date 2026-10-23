# 2026-10-23 — 수집 방식·데이터 확장·아키텍처 문서

[날짜 목차](2026-10-23.md) · [현재 handoff](../../handoff.md)

## DOCS-03 수집 상태와 확장 범위 (21점)

- 사용자 요청에 따라 `AGENTS.md` → handoff → plan을 읽고, 점수 21(영향3/확인가치3/확신3/후속해소2/범위보완2/비용1)로 문서·실행 상태 확인을 진행했습니다. BIZ-01은 사용자 요청으로 계속 후순위입니다.
- 다운로더·CLI·replay·pipeline·DAG·Compose/Helm 소스를 대조했습니다. 고정 Zenodo record의 명시적 다운로드와 과거 고정 구간 재처리를 구분하고, 새 관측값 정기 수집은 없음을 확인했습니다.
- 다른 출처의 CSV를 `public`으로 넣으면 BR-PVGen DOI/라이선스로 잘못 기록될 수 있어, 새 출처는 adapter와 계보 경로를 함께 확장해야 한다고 명시했습니다. 현재 V.1 전체는 Compose에 이미 처리되어 있습니다.
- [수집 안내](../guides/data-ingestion.md)에 실제 일정·상태, native/Compose 처리 명령, 기간·버전·출처 제한, 새 데이터/정기 수집 확장 순서를 작성했습니다. 추가 다운로드·스케줄 활성화·재처리·보고서 발행은 하지 않았습니다.

## 문서와 아키텍처

- [아키텍처](../architecture/system.md)에 전체 흐름·관리 서버 분리·환경별 저장소·일별 commit·보고서 snapshot/근거 비교와 구현/배포 경계를 작성했습니다. 네이티브/Compose/kind를 같은 DB로 오인하지 않도록 구분했습니다.
- [README](../../README.md)에 수집 주기와 데이터 추가를 직접 설명하고 기술 후속 CI·보고서 비교·복원·부하 근거를 반영했습니다. 과거 검사를 최신 검사로 표기한 문구를 수정했습니다.
- 출처·설치·DAG·기술 선택·구현 상태·문서 목차를 연결하고 DAG 안내의 과거 이미지 `0.4.0` 표기를 현재 참조로 수정했습니다. 기존 Airflow/kind 이미지는 최신 dashboard와 다름을 명시했습니다.
- 이번 작업은 코드·실행 상태를 근거로 한 문서 정리입니다. UI 스킬이나 연구 스킬·추가 에이전트를 사용하지 않았고 새로운 회귀 테스트·상시 검사 스크립트를 추가하지 않았습니다.

## 실행 상태 확인

2026-10-23 **13:11:04 KST**의 읽기 전용 확인입니다. 아래는 시점 관측값이며 지속 상태 보장이 아닙니다.

| 확인 | 결과 |
|---|---|
| Compose 컨테이너 | app-db/minio/dashboard 실행, Airflow api/scheduler/dag-processor/db 중지 |
| dashboard 이미지·준비 상태 | `solarops-worker:0.4.1-technical-final-20261023`, `/ready` → `ready` |
| kind 서비스 | 노드 실행, Running Pod 6개 모두 컨테이너 Ready |
| kind DAG | ingest_daily / quality_daily / report_monthly / backfill_manual 모두 `is_paused=True` |
| kind 배치 | Airflow `dag_run`의 `running` / `queued` 합계 0건 |
| GitHub | `TaeyanG4/solarops-audit`, `PRIVATE` |

확인에 사용한 명령(Windows의 WSL 배포판은 `Ubuntu-22.04`):

```powershell
docker ps -a --filter name=solarops-audit --format '{{.Names}}|{{.Status}}|{{.Image}}'
wsl.exe -d Ubuntu-22.04 -- bash -lc 'cd /mnt/h/dev/solarops_audit && KUBECONFIG=$PWD/artifacts/kubeconfig kubectl --context kind-solarops get pods -n solarops --field-selector=status.phase=Running'
wsl.exe -d Ubuntu-22.04 -- bash -lc 'cd /mnt/h/dev/solarops_audit && KUBECONFIG=$PWD/artifacts/kubeconfig kubectl --context kind-solarops exec -n solarops airflow-scheduler-0 -c scheduler -- airflow dags list --output json'
gh repo view --json nameWithOwner,visibility
```

진행/대기 합계는 kind의 `deployment/airflow-db`에 `psql -U airflow -d airflow`로 다음 읽기 쿼리를 실행했습니다:

```sql
SELECT count(*) FROM dag_run WHERE state IN ('running', 'queued');
```

원문 상태는 Git 제외 `artifacts/data-architecture-20261023/runtime.json`에 보존했습니다. 환경 변수·접속 암호·raw 데이터는 출력/커밋하지 않았습니다. 서비스 시작·중지·이미지 교체·DB 변경도 없었습니다.

## 검증과 전달

- `uv run solarops`의 `source fetch --help`, `replay --help`, `ingest --help`, `report --help`를 각각 실행해 문서 인수와 대조했습니다. 네이티브 공개 PS_001의 2024-04-03~04 구간 `replay` dry-run은 성공했고 DB/Parquet/보고서를 생성하지 않았습니다.
- Compose 실제 처리·보고서 명령은 CLI와 구성 파일로 확인했으며 이번에는 실행하지 않았습니다. 전체 다운로드·앱 전체 회귀·이전 부하/복원 검사를 반복하지 않았습니다.
- 기존 문서 검사(로컬 링크651개·스크립트 참조61개·원본 기획 checksum8개)와 `git diff --check`를 통과했습니다. handoff는 47줄·최근 요약8개이며 DOCS-03을 plan에서 제거했습니다. GitHub의 Mermaid 실제 화면 렌더링은 이번 확인 범위에 포함하지 않았습니다.
- 문서만 변경하므로 `[skip ci]`로 전달하며 기존 앱 회귀와 선택형 서비스 CI를 재실행하지 않습니다. 원본 ZIP·데이터·`docs/plan/`은 보존했고 로컬 runtime 증거는 Git에서 제외합니다.
