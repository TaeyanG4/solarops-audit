# v0.5.0 — 실제 증분 수집과 Airflow 병렬 측정

2026-10-23, 구현 `853de23` ([이미지·Git 증거](../releases/0.5.0.json)). 계산 버전은 `energy-interval-v2` 그대로입니다. [기계 판독 요약](incremental-v0.5.0.json) · [출처 계약](../ons-source-contract.md) · [작업 기록](../worklog/2026-10-23-incremental.md).

## ONS 수집 결과

| 환경·월 | 전체 입력 행 | 태양광 행 | 게시된 날짜 |
|---|---:|---:|---:|
| Compose 2026-10 | 365,040 | 69,696 | 21 |
| kind 2026-09 | 519,840 | 97,728 | 30 |
| kind 2026-10 | 365,040 | 69,696 | 21 |

- Compose 최초 수집은21일 게시, 같은 월 재실행은 **변경 날짜0개**입니다. 원본SHA와 기존 일별 manifest를 유지했습니다. 10월 원본 SHA-256은 `d6779647f5d803e1a140e184ee30086ce1f2c7d1bdab4a52cbdec1f96d6bccbe`입니다.
- 실제 KPO `solarops-collect-ons-months-gv7h6uaz`, Airflow run `scheduled__2026-10-23T05:00:00+00:00`가15:11:09~15:11:47 KST에 성공했습니다. UTC 스케줄의 이전/현재 월을 처리했으며 수동 날짜를 심은 성공 이력이 아닙니다.
- Compose와 kind의10월21개 날짜별 논리hash가 모두 같습니다. 원문 시각·MWmed·verified/forecast/unspecified를 유지하며 발전량 계산에 합산하지 않았습니다.
- 기존 공개 overview·PS_001 하루 series·보고서 목록 API의 전후 응답 바이트가 동일합니다. UI 코드를 수정하거나 전체 공개자료를 다시 계산하지 않았습니다.
- kind ONS DAG는 활성, 다음 실행은 **2026-10-24 14:00 KST**. 나머지6개 DAG는 paused, 진행/대기0건입니다. Compose Airflow3개 실행 컨테이너는0.5.0으로 생성했지만 중지 상태입니다. kind가 꺼져 있으면 수집도 실행되지 않습니다.

수정/지연/철회·중복충돌·실패 cursor·조직격리는 작은 통제 fixture로 검증했습니다. 실제 원천의 수정일이 도착한 것을 새로 관측한 시험은 아닙니다. 두 달보다 오래된 수정은 명시적 월 재수집이 필요합니다. 장기간 무인 운영과 외부 SLO는 검증하지 않았습니다.

## 실제 Airflow 공개 표본

동일 PS_001의2024-04-01~04(14,976행)를 **4개의 일별 KPO task**로 나눠, `max_active_tasks=1`과`2`를 비교했습니다. 각 시행에 새 PostgreSQL DB·MinIO 버킷·PVC 하위 경로를 만들고 원본은 기존 공개 파일을 사용했습니다. 생성/다운로드 시간을 처리량에 숨기지 않았으며, 아래 DAG시간에는 태스크 대기·Pod 시작 시간이 포함됩니다.

| 측정 | 직렬1 | 동시2 |
|---|---:|---:|
| 실제 DAG시간 | 36.675초 | 19.339초 |
| CLI trigger·상태 polling 포함 | 45.299초 | 29.658초 |
| worker CPU 합계 | 16.470초 | 20.468초 |
| worker 최대 RSS | 427.43MiB | 427.78MiB |
| 실제 동시 실행 Pod 최대 | 1 | 2 |
| 일별 결과 hash | 4개 | 4개 모두 동일 |
| S3 신규 객체 / 바이트 | 15 /149,174,614 | 동일 |
| DB inserted / updated | 33 /19 | 동일 |
| DB commit / rollback 통계 증가 | 95 /10 | 동일 |
| DB Pod CPU / 샘플 최대 메모리 | 0.350초 /37.98MiB | 0.308초 /54.09MiB |
| MinIO Pod CPU / 샘플 최대 메모리 | 0.609초 /128.71MiB | 1.086초 /183.73MiB |

두 실행은 모두 성공, task8개 exit0, 재시도 없이 완료했습니다. DB rollback 통계에는 SQLAlchemy 읽기 연결의 transaction 종료가 포함되며 실패한 처리10건이라는 뜻이 아닙니다. CPU/RAM 서비스 수치는 같은 호스트의 다른 활동·샘플링 영향을 포함합니다. S3수치는 최종 신규 객체수/용량이며 요청수나 업로드 지연 측정이 아닙니다.

**판단:** 이4개 독립 task 표본에서 동시2는47.3% 빨랐지만 총 workerCPU는24.3% 증가했습니다. 착수 전 기준(오류0·hash동일·workerRSS<2GiB·10분 이내,15% 이상 단축)을 충족해 **이 유형의 제한된 수동 배치에는2개를 권고**합니다. 기본 수집 DAG와 ONS 수집의 동시 실행은1개로 유지합니다.

한 물리 호스트의 kind에서 직렬→병렬을 각1회 실행했으므로 캐시·스케줄러 편향이 있습니다. 기존 단일 CLI가4일을 한 번에 처리하는 방식과 비교한 결과는 아닙니다. 매 task가 같은 파일을 읽는 비용도 포함됩니다. 다중 노드·장시간 부하·최대 처리량 또는 병렬4개 이상을 검증했다고 해석하지 않습니다.

재현: [DAG 운영과 측정 명령](../runbooks/dags.md#공개-dag-병렬-측정). 원본 결과·Pod로그·자원 표본은 Git 제외 `artifacts/dag-benchmark-1792735720/`, 실제 겹침·배포·수집 증거는 `artifacts/incremental-20261023/`에 보존합니다. DB/버킷/원본/완료Pod는 삭제하지 않았습니다.

## 검사와 배포

- 오프라인 **136통과·14제외**. 제외는 선택형 인프라/환경 검사이며 통과로 집계하지 않습니다.
- 별도 실제 PostgreSQL/MinIO **13통과**. 새 수집의 cursor rollback·정정·철회·조직 격리를 포함합니다. 테스트용 서비스는 종료하고 보존했습니다.
- Airflow local/Kubernetes 모드 각각 **7DAG import·template 성공**, import오류0. 첫 이미지의 safe-mode 탐색 누락은 수정 후 다시 확인했습니다.
- Compose 앱·kind Airflow/KPO를0.5.0으로 반영했고 `/health`, `/ready`, ONS status/day API를 확인했습니다. 원래 공개 API응답3개는 그대로입니다.
- Python3.12와 기존 잠금 의존성을 유지했습니다. 새 런타임 패키지·Kafka/Spark·별도 클러스터·외부 공개 배포를 추가하지 않았습니다.
- 구현 `853de23`의 [CI39910321487](https://github.com/TaeyanG4/solarops-audit/actions/runs/39910321487)는 Ubuntu/Windows 각각137통과·13제외, 합성 데모·복원·패키징 성공입니다. 로컬에서 권한 때문에 제외한 symlink 경로이탈 검사도 CI에서 통과했습니다.
