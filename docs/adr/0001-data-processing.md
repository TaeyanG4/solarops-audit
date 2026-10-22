# ADR 0001 — bounded Python/Arrow + DuckDB

수락. DuckDB는 CSV 필터·외부 정렬에 사용하고, Python은 발전소별 하루만 처리합니다. Arrow는 명시 스키마의 ZSTD Parquet를 씁니다. DuckDB 메모리 한도 512MB, 스레드 2. 실제 전체 실행의 프로세스 peak는 이외 Python/Arrow 메모리를 포함해 714MiB였습니다.

추적 필드는 Parquet 열에, 변경 가능한 소스의 추가 필드는 raw_json에 보존합니다. 일별 집계/이슈/사건은 실행 버전에 묶인 JSON payload로 저장하고 조직/발전소/일자/규칙/시각대 활성 인덱스를 별도 테이블로 둡니다. PostgreSQL payload는 SQL JSON 연산자로 조회할 수 있습니다. 이는 첫 버전에서 컬럼 확장마다 파괴적 마이그레이션을 피하기 위한 결정입니다.

오프라인 Windows 경로는 SQLite+로컬 객체 파일, 실제 서비스 경로는 PostgreSQL+MinIO입니다. 두 경로는 동일한 분석/트랜잭션 코드를 사용합니다. SQLite는 단일 로컬 사용을 위한 편의 기능이며 PostgreSQL 운영 검증을 대체하지 않습니다.
