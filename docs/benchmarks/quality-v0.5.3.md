# v0.5.3 — 독립 산출물 검토 후 경계 보완

2026-10-23. 평가 커밋 `adc75001360a7`의 [R1 원문과 수용 판단](../reviews/2026-10-23-artifact-r1.md)에 따른 수정입니다. 평가 점수는 수정 전 근거이며 새 평가 결과로 바꾸지 않습니다.

## 변경과 확인

| 경계 | 수정·범위 | 확인 |
|---|---|---|
| Python/SQL 시각 형식 | 양쪽이 해석하는 확장 날짜/시각과 명시 오프셋만 허용. SQL 파싱 불가행 우선 검증 | compact/week date/임의 구분자/7자리 소수초 기존 검사에서 수정 전4실패. 정상 UTC/오프셋과 v2 계산 유지 |
| BR 범위 축소 | 요청 내 기존 게시 날짜가 새 전체 관측 범위 밖으로 빠지면 `SOURCE_RANGE_SHRINK`. 첫 날짜 게시 전 거부 | 기존 targeted replay 검사에 앞/뒤 날짜 제거·전체 제거 확장. 이전 모든 active 보존. 요청 밖 날짜는 그대로 |
| 보간 여부 불명 | 일별 계산 값은 그대로. 보고서/화면에서 전부 불명·혼합·명시 False 구별 | DST/보고서 기존 검사에 각 경우 추가. 수정 전2실패. HTML과 브라우저에서 불명·33.33% 확인/불명1·0% 구별, 과거 보고서 바이트 보존 |
| 오류 정보 | BR catalog/quarantine와 CLI에 허용 코드·안전한 fallback만 기록. 고정 사용법 문구만 그대로 허용 | 기존 실패 게시 검사에 sentinel 값의 DB/파일/CLI 비노출 확장. 같은 검사 PostgreSQL에서도 실행 |
| 릴리스·재현 | Makefile도 release sync/check 대상. MinIO source SHA256·base digest 고정 | 기존 DAG 검사와 release check 사용. MinIO 빌드 및 새 격리 서비스 검사. 실행 중 기존 MinIO와 별도 |

새 영구 테스트 함수·검증 전용 스크립트를 추가하지 않았습니다. 데이터 의미·게시·비밀 경계에 관련된 기존 검사를 확장했습니다. 전후 실패와 검사 실행·배포·제외 항목은 [수행 기록](../worklog/2026-10-23-quality-r2.md), 기계 판독 요약은 [JSON](quality-v0.5.3.json)에 구별합니다.

## 의미 보존

계산 버전은 `energy-interval-v2`입니다. 보간 true 비중은 전체 관측 슬롯을 분모로 하는 기존 지표이며, 불명 플래그를 False로 바꾸지 않습니다. 새 보고서에는 `observed_slots`, `interpolation_unknown_slots`를 포함하고 전부 불명이면 요약 `interpolation=null`입니다. 일부 불명은 확인된 true 비중과 불명 수를 함께 표시합니다. 기존 지표·계보·과거 HTML/CSV/manifest를 소급 변경하지 않습니다.

BR-PVGen은 고정 배포 자료의 선택 기간 upsert이며 사라진 날짜의 자동 철회는 지원하지 않습니다. 기존 날짜가 빠지는 입력을 성공으로 기록하는 대신 거부합니다. 이는 ONS의 명시적 월 snapshot/철회 계약과 다릅니다. 이 범위에서 철회 지원을 추가하거나 원본을 삭제하지 않았습니다.

## MinIO 빌드 입력

공식 source archive SHA256 `be6d0bd3696c3a13a35f02d3a0280b64319c67918b4501c5c3d87f96d000085c`, Go/Debian의 multi-platform manifest digest를 [Dockerfile](../../infra/docker/Dockerfile.minio)에 고정했습니다. `docker build -f infra/docker/Dockerfile.minio -t solarops-minio:2025-10-15-pinned .`은 기존 Go 빌드 캐시를 사용해 성공했습니다. 캐시 없는 독립 재현 빌드나 두 호스트의 바이너리 일치 검사가 아닙니다.

검증 이미지 ID는 `sha256:ba58cd8f4781043abf8d5c3a3b656d4aba181dc5415ce7e884819b522a3b3955`입니다. `--version`은 여전히 `DEVELOPMENT.GOGET / go1.24.8 linux/amd64`이며 소스 release와 구별합니다. 새 격리 MinIO에서 기존 서비스 검사를 수행했고 실행 중 저장소 컨테이너·볼륨은 교체하지 않았습니다. 원본 다운로드 파일·시험 컨테이너도 보존합니다.

## 화면 확인

Agent Browser의 작업 전용 세션과 격리 SQLite/합성 3슬롯씩 사용했습니다. 전체 불명 1440px, 혼합 390px, 명시 False 768px에서 실제 표시·가로 넘침 없음·페이지 오류 없음을 확인했습니다. 전체 UI 재검사나 접근성 인증을 주장하지 않습니다. 캡처와 서버 로그는 Git 제외 `artifacts/portfolio-quality-20261023/`에 보존합니다.

범위 계산은 작은 합성 7일 정상 hash와 기존 공개 PS_001 파일의 min/max를 대조했습니다. 다운로드·전체 공개 재처리 없이 수행했고, [재현 명령](../worklog/2026-10-23-bounds-reproduction.md)을 별도로 보존합니다. 이 범위 측정은 전체 ingest 성능이 아닙니다.
