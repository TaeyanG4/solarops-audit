# 2026-10-23 기술스택·자료 진위 점검

## 출처와 실제 계산

- AUDIT-01 22점(3/3/3/3/3/2): 실행 가능한 최고 우선순위로 읽기 전용 실사. 고객 입력이 없는 BIZ-01은 계속 대기합니다.
- Zenodo 현재 메타데이터와 원본 4개, 압축 해제 CSV 102개, 공개 계보 SHA-256 103개를 대조했습니다. 원본 전체 재다운로드·삭제는 하지 않았습니다.
- 대표 raw 3개·Parquet 2개를 실제 MinIO에서 읽고 원본 독립 계산을 DB·API·보고서·kind 결과와 대조했습니다. 19,752.692125 kWh 일치, 공개/합성 inventory와 실패 주입 기록을 분리했습니다.
- v1 native/Compose 전체 12,572개 논리 해시·지표 및 Compose v1/v2 지표(버전 제외) 일치를 재확인했습니다. 기본 native DB는 v1 보존본으로 v2는 0개입니다.
- 방법·수치·검증 범위는 [실사 보고서](../benchmarks/stack-authenticity-20261023.md), [요약 JSON](../benchmarks/evidence/stack-authenticity-20261023.json)에 있습니다.

## 실행 기술과 문서 정정

- 실행 이미지 코드 36개 해시·라이브러리·DB dialect를 확인하고, Airflow 메타DB 44개 DAG 실행·80개 KPO 태스크 및 공개 시나리오 9개 Pod 대응을 읽었습니다.
- kind 서비스 Pod 6개 Ready이나 DAG 4개는 paused, Compose Airflow는 중지 상태입니다. kind v2는 공개 하루만 처리한 별도 DB임을 명시했습니다.
- MinIO `DEVELOPMENT.GOGET`과 빌드 recipe tag의 차이, Helm chart app_version과 실행 Airflow 버전의 차이를 기록했습니다. 실제 S3 사용과 바이너리 재현 빌드 보증을 구별합니다.
- 초기 보조 검사에서 S3 stream 자동 닫힘·CSV 빈 셀 표현 차이를 만나 audit reader를 수정했습니다. scheduler에는 앱 DB 환경이 없어 기본 SQLite 조회가 실패했고 실제 app-db에 read-only SQL로 확인했습니다. 제품 오류로 집계하지 않습니다.
- README·출처·기술스택 문서에서 실사 근거로 바로 연결하고, 원본·기존 결과와 서비스 상태를 보존했습니다. 상세 원본 증거는 `artifacts/stack-authenticity-20261023/`에 있습니다.

## 검증·전달

- `uv run python scripts/validation/check_docs.py`: 로컬 링크 462개·스크립트 참조 55개·원본 기획 checksum 8개 통과. `git diff --check`와 요약 JSON 검사를 통과했습니다.
- handoff 38줄·최근 요약 8개, 완료 AUDIT-01은 plan에서 제거했습니다. 이번 변경은 문서와 검증 요약이며 로컬 앱 회귀·전체 재처리를 새로 실행하지 않았습니다.
- 비공개 GitHub main에 문서·비밀/원본행 없는 요약 JSON을 반영합니다. 원본 데이터·서비스 상태는 유지했습니다.
