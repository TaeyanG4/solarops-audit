# 입력·게시 무결성과 릴리스 정렬

## DATA-02 · PUB-01
- 독립 검토의 4개 재현 결함을 수정했습니다. 인버터 ID는 정규 십진 int64만 허용하고 `01/1` 혼용은 범위 계산/행 변환 양쪽에서 거부합니다. 정상 입력 계산 버전은 v2를 유지합니다.
- ZIP은 개별 CSV의 EOF/CRC·크기·fsync 완료 후 원자적으로 최종 경로에 연결합니다. 중단 파일·원본은 보존하며 ZIP 전체가 하나의 트랜잭션인 것은 아닙니다.
- 일별 active를 배치 시작 시점과 비교해 교체합니다. metadata도 같은 트랜잭션에 게시하며, 겹친 작업은 `PUBLICATION_CONFLICT`, 다른 날짜의 metadata 경합은 `PLANT_METADATA_CONFLICT`로 이전 결과를 보존합니다.
- 버전 문자열에 순서를 부여하지 않습니다. 이미 성공 게시했다가 다른 버전으로 교체된 날짜를 복원하려면 `ingest/backfill --restore`가 필요합니다. 복원도 동시성 검사를 생략하지 않고 이전 run ID와 요청을 기록합니다. 배치 전체가 아니라 날짜별 원자성입니다.
- 관련64검사 통과 후 실제 PostgreSQL의 INSERT rowcount 차이를 발견해 `RETURNING`으로 수정했습니다. 격리 PostgreSQL/MinIO11검사 통과(17.26초); 기존 서비스·원본은 변경하지 않고 시험 컨테이너는 중지·보존했습니다.

## OPS-08 · OPS-09 완료
- `src/solarops/release.json`을 버전 명세로 삼고 Compose/Helm/작업 도구의 선언을 검사합니다. v0.4.2, 계산 v2이며 커밋·이미지 ID는 [릴리스 증거](../releases/0.4.2.json)에 연결했습니다. dashboard·kind 롤아웃 완료, Compose Airflow도 새 컨테이너로 준비 후 중지 상태입니다.
- Airflow3.3.2/Kubernetes provider10.24.0의 기존 이미지 설치 목록을 제약 파일로 보존했습니다. 공식3.3.2 제약은 provider10.22.0이라 그대로 적용하지 않았습니다. 기반 이미지 digest를 고정하고 `pip check`를 빌드에 포함했습니다.
- 실행/보고서에 릴리스·허용된 Airflow dag/run/task/attempt·Pod UID를 연결하고 진단에 단계·행 수·오류·관련 시도를 추가했습니다. 오래됐다는 이유만으로 실패 상태를 쓰지 않습니다. 기존 UI/API 필드는 유지합니다.
- DuckDB spill은 컨테이너의 쓰기 가능한 `/tmp` 하위 연결별 경로로 지정했습니다. 큰 공개 작업이나 병렬 확대의 성능 검증을 완료한 것은 아닙니다.
- 전체 로컬133통과·12제외 후 실제 서비스12통과. 구현 `2f42cbe`의 [CI](https://github.com/TaeyanG4/solarops-audit/actions/runs/39906673530)는 Ubuntu/Windows 각각134통과·12제외, 릴리스 선언·합성 데모·복원·패키징 통과입니다.
- Native/Compose/실제 KPO의 합성7일 해시·보고서18필드 일치(추정832.424kWh), KPO1차 실패/2차 성공과 Pod/active 연결, 공개 응답3개 전후 동일을 확인했습니다. [조건·ID·명령·한계](../benchmarks/integrity-v0.4.2.md). 상세 증거는 Git 제외 `artifacts/integrity-delivery-20261023/`입니다.

## 다음 조건부 항목 점검
- DATA-03 후보로 [ONS 시간별 발전 자료](https://dados.ons.org.br/dataset/geracao-usina-2)의 CKAN metadata와 현재2026-10 CSV 앞16,384바이트만 읽었습니다. metadata 갱신2026-10-22T22:08:53, CC Attribution 표시, 원본은 약47.4MB이며 전체 다운로드·적재는 하지 않았습니다.
- 원천 설명은 일부 작은 발전소 그룹이 **예측**이고 사후 수정도 가능함을 명시합니다. CSV 시각은 offset 없음, 시간별 간격이며 기존 BR-PVGen15분 인버터/POA/용량 계약과 다릅니다. 실제 원천 URL·라이선스 버전·시각 의미·단위·예측 제외/분리 계약을 확정하기 전 기존 public로 변환하지 않습니다.
- DATA-03은 원천 계약 의존, PERF-03은 처리시간/자원 목표 의존으로 남깁니다. spill 경로는 준비했지만 측정하지 않은 병렬 이득을 주장하거나 DAG 동시성을 늘리지 않았습니다. 연구 스킬·추가 독립세션·영구 UI 회귀 스크립트는 사용하지 않았습니다.
