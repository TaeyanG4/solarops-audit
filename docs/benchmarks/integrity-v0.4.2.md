# v0.4.2 입력·게시·릴리스 검증

2026-10-23 Asia/Seoul. 구현 커밋 `2f42cbe04c4d4d2f47d4e26a929f792864abe749`.
[릴리스 명세](../../src/solarops/release.json) · [이미지/커밋 증거](../releases/0.4.2.json) · [수행 기록](../worklog/2026-10-23-integrity-delivery.md)

## 재현 결함과 결과

| 경계 | 변경과 실행 증거 |
|---|---|
| 인버터 `01/1` 혼용 | 범위 계산과 정규화에 같은 canonical int64 계약 적용. 선행 0·부호·공백·소수·int64 초과 거부. 정상 입력 계산식은 유지 |
| ZIP 복사 중단 | 4바이트 기록 후 실패 주입: 최종 CSV 없음, partial 보존. 재시도/반복 추출 후 완전한 원본 바이트 일치 |
| 실패한 metadata 게시 | 20→30kW 입력에 before/during commit 실패 주입. `/plants`와 기존 active 해시 유지 |
| 역순·겹친 날짜 게시 | 배치 시작 때 active를 캡처하고 SQL 조건부 교체. absent/existing/동일 버전 경합 모두 느린 작업 차단, 승자 재시도 해시 동일, 겹치지 않은 날짜 보존 |
| 의도적 과거 복원 | 게시 이력의 v1→v2→v1은 기본 거부. `--restore` 요청 시만 새 실행으로 게시하고 이전 run ID 기록 |
| 실제 DB 차이 | 첫 PostgreSQL 검사에서 드라이버 rowcount로 성공을 판별할 수 없음을 확인. `RETURNING` 기반 판별로 수정 후 전체 서비스 검사 성공 |

개별 CSV와 개별 날짜가 완료 경계입니다. ZIP 전체나 여러 날짜 배치를 하나의 트랜잭션으로 보장하지 않습니다. 정상 완료한 앞 날짜는 뒤 날짜가 실패해도 유지됩니다. metadata는 마지막으로 성공 게시한 입력이며 각 날짜 manifest에도 그 날짜의 metadata를 보존합니다.

충돌은 자동으로 덮어쓰지 않습니다. 운영자는 현재 active/source version을 확인하고 필요한 범위로 재시도합니다. `--restore`도 동시성 검사를 우회하지 않습니다. 버전 문자열의 사전 순서나 작업 시작 시각으로 데이터의 최신성을 추측하지 않습니다. 새 버전 이름으로 주어진 입력의 업무상 최신성은 운영자 책임입니다.

## 실제 실행한 검사

| 검사 | 결과 |
|---|---|
| 기존 계약·파이프라인·게시·무결성 | 64통과 |
| 전체 오프라인 | 133통과·12제외, 25.87초. 이후 서비스 추적 사례를 추가했으며 해당 사례는 실제 서비스 검사에 포함 |
| 구현 커밋 CI | [39906673530](https://github.com/TaeyanG4/solarops-audit/actions/runs/39906673530), Ubuntu134통과·12제외(19.69초), Windows134통과·12제외(24.04초). 릴리스 선언·합성 데모·복원·패키징 성공 |
| 격리 PostgreSQL16.10/MinIO | 최종12통과, 18.51초. 새 임시 자격정보·테스트 조직/버킷, 기존 서비스와 분리. 완료 후 컨테이너 중지, 데이터 보존 |
| Airflow local/KPO 템플릿 | 각각 DAG4개, public/synthetic 매개변수, import 오류0 |
| Docker build | worker/Airflow 성공, Airflow `pip check` 성공. 기본 이미지 digest·앱 uv.lock·Airflow 전이 의존성 버전 제약 고정 |
| Native / Compose / 실제 Airflow KPO | 합성 DEMO_01 2024-04-01~08 미만, `release-042-20261023`, 일별 논리 해시7개 모두 일치 |
| 보고서 계약 | 동일 7일 추정832.424kWh. 기간·선택 범위·시간대·계산 버전·출처 종류·품질·지표·후보 등18필드 일치 |
| 배포 보존 | 공개 2024-04 overview, PS_001 4월1일 series, 기존 보고서 `5fd1a0be-9514-4f39-ad76-06f80c157ec5` HTML의 응답 SHA 전후 동일 |

첫 날짜 논리 해시: `2f91b47555211ff7bea962de4c928cec77e5af3a7667de4a8ef4a14ecdbe7fc4`.
환경별 run UUID·객체 위치·조직·실행 시각은 다릅니다. 전체 보고서 파일의 SHA가 같다는 주장이 아니며 계산 내용과 보고서 계약을 비교했습니다. 이 시험은 합성 표본이며 공개 전체 재처리·장시간 성능 시험이 아닙니다.

## Airflow 재시도와 추적

- 실제 DAG run `release042-retry-20261023`: 1차 `INJECTED_DURING_COMMIT`, 2차 성공. 실패 partition `9d3cfacd-0ee1-4597-8294-cad97e0e2356`은 `publishing` 단계와 처리 행 수를 보존합니다.
- 실패 Pod UID `8e78f43f-ff2d-4769-a094-58ab75b1da36`, 재시도 Pod UID `46344d8f-724f-4fa2-8aec-afeff1139e28`. 동일 dag/run/task와 다른 attempt가 저장되었습니다.
- 기존 `inspect-runs --run-id` / 진단 API가 실패 기록→관련 성공 시도→현재 active를 연결합니다. 이어 실행한 7일 대조 작업으로 active가 또 바뀌어도 관련 재시도와 현재 결과는 구분합니다.
- 나이만으로 실패를 확정하거나 상태를 고치지 않습니다. 과거 실행의 없던 release/Pod 필드는 추측해 채우지 않습니다. 현재 UI의 기존 진단 표시는 유지하며 추가 상세 필드는 CLI/API로 조회합니다.

## 전달과 한계

Compose dashboard/worker/Airflow와 kind Airflow/KPO 선언을0.4.2로 통일했습니다. dashboard와 kind 서비스는 새 이미지로 실행 중이며 Compose Airflow는 새 컨테이너를 준비한 뒤 중지 상태를 유지합니다. 시험 후 DAG4개를 모두 paused로 되돌렸습니다. 기존 완료 Pod·이미지·원본·보고서를 보존했습니다.

`uv run python scripts/release/release.py check`로 선언/제약 hash를 확인하고 `sync`로 버전을 반영한 뒤 `uv lock`을 갱신합니다. 구현을 커밋한 뒤 `build`하면 Git revision을 이미지 label·런타임에 넣고 이미지 ID를 별도 증거에 기록합니다. 일반 `docker compose build`로 revision 없이 빌드하면 `unrecorded`로 표시되므로 정식 전달에는 이 릴리스 명령을 사용합니다. Airflow 제약은 기존 검증 이미지의 전이 버전 목록이며 wheel별 해시 잠금은 아닙니다.

로컬 상세 근거: Git 제외 `artifacts/integrity-delivery-20261023/`의 `offline.xml`, `services.xml`, `build.log`, `parity.json`, `kpo-diagnostics.json`, `kpo-attempts.json`, `release-pods.json`, `public-before.json`, `public-after.json`. 초기 서비스 검사 실패 원인과 수정은 위 표에 기록했습니다. 원본 데이터나 secret은 Git에 올리지 않습니다.
