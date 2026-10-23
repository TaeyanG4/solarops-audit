# 핵심 설계 질문 5개

[제출 요약](SUBMISSION.md) · [시연 안내](DEMO_GUIDE.md). 아래는 코드와 근거를 연결한 답안이며, 지원자 본인의 면접 설명 숙련도를 자동 검증한 결과가 아닙니다.

## 1. 왜 원본 SHA와 논리 해시를 따로 두었는가?

SHA-256은 입력 바이트의 동일성을, 논리 해시는 실행 ID·시각을 제외한 정규화 결과의 동일성을 확인합니다. source_version 라벨·조직/발전소/시간대/계산 버전은 포함하므로 같은 라벨·설정 안에서 비교해야 합니다. 입력 이름이 같아도 내용이 달라지면 별도 버전으로 취급해야 합니다. 원본 보간과 표본 수까지 논리 내용에 포함해 계보를 잃지 않습니다.

코드: [ObjectStore 원본 보존](../../src/solarops/storage/minio.py), [정규화](../../src/solarops/normalize/parquet.py), [파이프라인](../../src/solarops/pipeline.py). 근거: [입력/게시 경계 검사](../../tests/test_publication_boundaries.py), [v0.4.2](../benchmarks/integrity-v0.4.2.md).

## 2. 객체 업로드와 DB 커밋 사이에 실패하면 무엇이 보이는가?

객체 저장 후 검증과 DB의 활성 포인터 전환을 수행합니다. 커밋이 실패하면 이전 활성 결과를 읽고 미게시 객체는 증거로 남습니다. BR-PVGen은 일별 게시라 batch 후반 실패 시 앞 날짜는 완료될 수 있습니다. ONS는 한 월의 변경 manifest와 성공 cursor를 같은 트랜잭션으로 게시하고, 기대 cursor가 달라졌으면 충돌로 거부합니다. DB와 S3를 묶은 분산 트랜잭션이라고 주장하지 않습니다.

코드: [Catalog](../../src/solarops/storage/postgres.py), [ONS publish/commit](../../src/solarops/acquisition/ons.py). 근거: [실패 복구 데모](../../scripts/demo/portfolio_demo.py), [무결성 ADR](../adr/0008-storage-integrity.md).

## 3. ONS를 기존 추정 발전량과 합산하지 않는 이유는?

ONS 단위는 MWmed이고 공식 사전은 시간대·구간 시작/끝을 명시하지 않습니다. verified/forecast/unspecified도 혼재합니다. 따라서 원문 시각과 유형을 보존하고 ts_utc=null, energy_conversion=false로 둡니다. 시간대와 간격의 가정을 검증하지 않고 kWh를 만들면 다른 원천과 그럴듯하게 합산되지만 의미가 달라질 수 있습니다.

코드: [ONS CONTRACT와 parse](../../src/solarops/acquisition/ons.py). 근거: [공식 사전·라이선스·유형 계약](../ons-source-contract.md), [파싱 검사](../../tests/test_contracts.py).

## 4. 왜 Airflow와 Kubernetes를 사용하고 Kafka/Spark는 넣지 않았는가?

Airflow는 일정·의존성·재시도·이력, KubernetesPodOperator는 작업별 CLI의 자원/권한 격리를 담당합니다. LocalExecutor가 KPO를 호출하는 구조이며 KubernetesExecutor가 아닙니다. 월별 CSV를 확인하는 배치 요구에 Kafka 스트리밍은 필요하지 않았고, DuckDB의 외부 정렬로 처리 가능한 이 규모에서 Spark의 분산 운영 비용을 정당화하지 못했습니다.

코드: [공통 DAG factory](../../dags/solarops_factory.py), [ONS DAG](../../dags/solarops_ons_daily.py), [CLI](../../src/solarops/cli.py). 근거: [KPO 선택](../adr/0003-kpo-not-executor.md), [기술 선택과 재검토 조건](../architecture/technology-stack.md).

## 5. 47.3% 단축을 어디까지 주장할 수 있는가?

단일 kind 호스트의 동일 PS_001 공개4일을 4개 일별 task로 실행했고, 동시1/2의 DAG wall time을 비교했습니다. 4개 결과 hash는 같고 오류0이지만 CPU 합은24.3% 늘었습니다. 직렬 후 병렬 각1회, 캐시·기동 비용 포함이므로 일반 처리 성능이나 다중노드 선형 확장성으로 해석할 수 없습니다. 기본 정기 수집 동시성은1로 유지합니다.

코드: [벤치마크 DAG](../../dags/solarops_public_benchmark.py), [측정 도구](../../scripts/validation/k8s_benchmark.py). 근거: [수치·환경·원본 JSON](../benchmarks/incremental-v0.5.0.md).
