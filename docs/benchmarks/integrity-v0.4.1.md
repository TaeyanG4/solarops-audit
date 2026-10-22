# v0.4.1 — 입력·조회·공개 무결성

2026-10-23, 자체 실행 결과. 독립 외부 검토는 PENDING이며 고객 데이터·매출·실제 고장 정확도와 무관하다. 계산 v2는 유지한다.

## 재현과 수정

| 경계 | 수정 전 | 수정 후 |
|---|---|---|
| metadata 중복 헤더/행 폭 | 모호한 입력 3개 수용 | 계약 오류로 거부 |
| 원본 보존 후 입력 변경 | 결과와 기록 SHA 불일치 | 보존 raw만 처리 |
| 같은 버전의 다른 동시 입력 | SQLite 양쪽 성공 | 한쪽 성공, 한쪽 명시 충돌 |
| API 저장소 부재 | readiness가 버킷 생성 | 생성 없이503 |
| 보고서 파일 부재 | 비제어500 | 경로 비노출404 |
| 원본 복사 중 접근·변경 | 부분 파일 노출/잘못된 경로 잔존 | 검증한 staging만 원자적 링크 공개 |
| 오래된 보고서의 늦은 완료 | 최신 포인터가 과거로 역행 | 최신 조회 시작 시각 유지, 두 이력 보존 |

최초7실패 `artifacts/integrity-audit-before.log`, 추가3실패/2통과 `artifacts/publication-before.log`를 보존했다. 수정 후 경계10개와 공개5개가 통과했다. 실제 PostgreSQL·MinIO5개는 transaction 읽기 전용, 동시 버전, 보고서 역순 완료·업로드 실패·DB rollback도 포함한다.

단일/불연속 저출력 슬롯이 사건으로 집계되지 않는 회귀를 추가했고 화면 표현을 명확히 했다. DST/비UTC/무효값/유효0의 기존 회귀를 유지했다. 정상 계산 v2를 바꾸지 않았으므로 전체51개 재처리를 반복하지 않았다.

## 검증 결과

| 항목 | 결과 |
|---|---|
| Windows 전체 오프라인 | 112 passed, 6 skipped (서비스5·symlink 권한1) |
| WSL Ubuntu 전체 오프라인 | 113 passed, 5 skipped (서비스 opt-in) |
| 실제 PostgreSQL·MinIO | 5 passed, 경고 없음 |
| 합성 독립 데모 | 이전7개 활성 파티션 보존, 재처리 해시 일치 |
| SQLite/로컬 복원 | 34파일 SHA·무결성·과거 보고서·raw replay 확인 |
| PostgreSQL/MinIO 복원 | 전용 DB/버킷, 27객체 보존·과거 보고서·raw replay 확인 |
| 앱/개발 의존성 감사 | pip-audit, 잠긴 전이 의존성 포함, 알려진 취약점0 |
| DAG import | v0.4.1 컨테이너의4DAG 및 공개/합성 템플릿, 오류0 |

의존성 감사는 PyPI 알려진 취약점 기준의 시점 검사이며 OS 이미지·Airflow의 별도 환경·MinIO 소스까지 검사한 결과는 아니다. TestClient를 httpx2 2.16.0으로 전환해 기존 사용 중단 경고를 해소했다. GitHub Actions checkout v6/setup-uv v7/upload-artifact v6의 commit SHA를 고정했다.

증거: `artifacts/services-v041.log`, `artifacts/dependency-audit-v041.json`, `data/portfolio-v041-verified/evidence.json`, `data/restore-v041-verified/evidence.json`, `data/service-restore-v041-verified/evidence.json`.

## 배포와 패키징

최종 Windows/WSL 회귀·서비스5개·wheel 빌드는 통과했다. 공개 PS_001/2024-04-03 하루를 재처리해 기존 논리 해시 일치를 확인하고 새 4월 보고서3종의 SHA 검증 다운로드도 통과했다. 최종 Compose/kind 시나리오·브라우저·원격 CI·소스 ZIP은 현재 확인 중이다. 실행이 끝난 결과만 이 절에 갱신한다. 이미지 이력은 [image-versions.json](../image-versions.json)에 보존한다.

배포 검증 도중 Windows에서 편집된 셸의 CRLF로 kind refresh가 실행 전에 중단됐다. LF로 수정하고 문서 검사에 셸/Make LF 검사를 추가했다. DAG 검사기는 Airflow 전용 컨테이너에서 실행해야 하며 앱 네이티브 환경에는 Airflow가 없다. 실패 로그도 보존한다.
