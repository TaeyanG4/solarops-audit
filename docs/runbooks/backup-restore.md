# 백업과 복원 검증

[복구 판단](recovery.md) · [현재 상태](../IMPLEMENTATION_STATUS.md)

`uv run python scripts/validation/backup_restore_drill.py`는 새 폴더에 합성 일주일 자료를 만들고 SQLite와 로컬 파일을 백업한 뒤 다른 폴더로 복원한다. 기존 폴더는 거부하며 삭제하지 않는다. 사용자 DB나 실행 중인 서비스를 백업하는 도구가 아니다.

## 확인하는 계약

1. 합성 수집과 보고서 생성이 모두 끝나 쓰기가 없는 전용 경로를 사용한다. SQLite backup API로 WAL 내용까지 일관된 DB 사본을 만들고 `integrity_check`를 확인한다.
2. 원본·Parquet·시계열·보고서를 복사하고 파일별 SHA-256 목록을 남긴다. 파일 변경과 별도 손상 사본을 탐지한다. 실행 중 일반 파일 복사의 일관성을 보장한다고 주장하지 않는다.
3. 새 복원 폴더의 카탈로그에만 경로를 재배치한다. 원본 백업 DB와 보고서 HTML/CSV/manifest 바이트는 유지한다. 과거 manifest의 출처 URI는 당시 경로이며 `evidence.json`의 original_root→restored_root 매핑으로 복원 위치를 찾는다.
4. 복원한 DB로 현황·시계열·과거 보고서 API를 읽고 원본 SHA, 7개 활성 파티션의 논리 해시를 확인한다. 복원된 원본만으로 재처리해 해시가 같고 새 보고서를 만들 수 있어야 한다.

출력: `backup-manifest.json`, `evidence.json`, `original/`, `backup/`, `restored/`, 손상 탐지용 `damaged-probe/`. 모두 새 출력 폴더 안에 남는다. 같은 호스트의 로컬 경로 재배치 시험이며 OS 간 URI 변환과 외부 저장소 복원은 포함하지 않는다.

## PostgreSQL·MinIO 합성 복원

로컬 Compose PostgreSQL·MinIO가 실행 중이면 `uv run python scripts/validation/service_restore_drill.py --output data/service-restore-new`로 실행한다. 새 출력 폴더, 전용 합성 DB 2개와 버킷 2개를 만든다. 기존 앱 DB/공개 자료 버킷은 변경하지 않는다. 생성 자원은 증거로 남기며 자동 삭제하지 않는다.

단일 생산자의 수집·보고서 생성이 끝나고 running/validated가 없는 것을 확인한 뒤 pg_dump custom 형식과 모든 참조 객체를 파일로 저장한다. DB dump SHA, 카탈로그 전체 논리 해시, 객체 key/크기/SHA, pg_dump 버전과 이미지 ID를 기록한다. 비밀값은 출력에 넣지 않는다.

새 DB에 pg_restore하고 새 버킷에 저장한 객체를 업로드한다. 복원 카탈로그의 S3 버킷 URI만 치환하며, 과거 보고서 파일은 바이트 그대로 유지한다. 과거 manifest의 버킷은 backup-manifest의 original_bucket→restored_bucket 매핑으로 해석한다. 복원 API·과거 보고서·raw SHA·7개 파티션 재처리 해시·새 보고서와 원본 전체 카탈로그/객체 비변경을 검사한다.

이 시험은 **같은 서버의 별도 DB/버킷을 이용한 논리 복원**이다. 다른 호스트/장애 디스크/동시 생산자에서 복원한 결과가 아니며 측정 시간을 운영 RTO/RPO로 쓰지 않는다.

## 고객 운영에 남은 조건

- 수집·보고서 생산자를 멈추거나, DB 스냅샷과 참조되는 불변 객체 목록의 일관성을 보장하는 배리어를 정의한다. DB dump만으로 객체가 복원되지는 않는다.
- DB 버전·스키마·앱 이미지 digest·계산 버전, 원본/정규화/시계열/보고서의 객체 key·크기·SHA를 저장한다. 접근 비밀값은 소스 ZIP이나 증거 JSON에 넣지 않는다.
- 별도 호스트/인스턴스와 외부 백업 저장소에서 장애 상황을 복원한다. raw SHA·활성 포인터·보고서 참조·재처리 해시·API를 다시 검사한다.
- 실제 복원 시간과 허용 데이터 손실(RTO/RPO), 저장 위치·암호화·접근 권한·보관 책임을 결정한다. 같은 디스크의 복사본이나 kind PVC는 재해복구 보장이 아니다.

삭제·보존 기간 적용은 이 시험에 포함하지 않는다. 실제 고객 자료 처리는 별도 이용 권한과 보관 합의가 전제다.
