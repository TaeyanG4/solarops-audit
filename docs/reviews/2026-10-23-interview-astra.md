# Astra — 독립 모의 면접관 평가

2026-10-23 (Asia/Seoul). 사용자가 요청한 독립 평가입니다. 실제 모델은 `gpt-6-astra`, 세션은 `/root/astra_interviewer`, 기준은 `66d63486722dfb7bc83418667c90db1cecfadbf6`입니다.

아래는 평가자의 최종 답변 전문입니다. 로컬 파일 링크를 기준 커밋의 GitHub 링크로 바꾸고 Markdown 줄 끝 공백을 정리했습니다. 외부 사람의 채용 평가나 합격 확률을 뜻하지 않습니다. [교차 확인·종합 판단](2026-10-23-interview.md) · [수행 기록](../worklog/2026-10-23-interview.md).

---

실제 평가 모델: **gpt-6-astra**
검토 기준: **HEAD `66d63486722dfb7bc83418667c90db1cecfadbf6`**, 앱 v0.5.1.

**신입·주니어 데이터 엔지니어 면접 초대를 추천합니다.** 데이터 품질과 실패 경계를 실제 코드로 다룬 포트폴리오입니다. 다만 저장소 품질이 지원자 개인의 구현·디버깅 능력을 증명하지는 않습니다. AI 활용이 공개된 만큼 면접에서는 작은 변경 과제로 설계 소유권을 확인하겠습니다.

중급 채용이라면 **이 프로젝트만으로는 보류**입니다. 지속 운영, 스키마 변경, 경보·복구 책임, 여러 호스트에서의 장애 대응까지 맡길 근거는 부족합니다. 이는 신입 포트폴리오의 제출 결격 사유와는 구분해야 합니다.

**점수: 83/100.** 제 주관적 포트폴리오 루브릭이며 합격 확률이나 지원자 개인 역량 점수가 아닙니다.

| 항목 | 점수 | 판단 근거 |
|---|---:|---|
| 데이터 계약·모델링 | 22/25 | 원본 보간·표본 수·추가 필드 보존, UTC 정규화, 중복 충돌 처리, ONS 의미 분리가 좋습니다. 카탈로그는 JSON payload와 애플리케이션 규칙에 많이 의존하며 스키마 진화 증거는 약합니다. |
| 신뢰성·복구 | 21/25 | 객체 선저장 후 조건부 활성 포인터 전환, 실패 시 이전 게시 유지, 동시 작업 충돌 및 과거 복원 통제가 구체적입니다. 비정상 종료 상태 조정과 ONS 오류 진단은 미흡합니다. |
| 아키텍처·기술 선택 | 16/20 | 공통 CLI, 실행기와 변환 로직 분리, 환경별 저장소 경계가 명확합니다. Airflow/KPO는 학습·검증 목적에 타당하지만 이 데이터 규모의 경제적 최적 선택까지 입증하지는 않았습니다. |
| 재현·검증 | 12/15 | 잠긴 앱 의존성, 양 OS CI, 합성 복구 데모와 서비스 검증 기록이 있습니다. 인프라 전체 잠금 및 외부 심사자가 바로 확인할 장기 증거의 완결성은 제한적입니다. |
| 설명·전달 | 12/15 | 숫자의 범위와 미검증 항목을 정직하게 설명합니다. 다만 문서량과 버전별 증거가 많아 평가자의 탐색 비용이 큽니다. 본인이 어떤 판단을 주도했는지는 면접 확인이 필요합니다. |

검토에서는 AGENTS→handoff→plan, 제출 문서, 아키텍처, ONS 수집기, 계산·정규화·카탈로그·게시 코드와 관련 테스트를 직접 읽었습니다. **기존 테스트 함수 3개를 메모리에서 직접 호출해 에너지·누락·동일 중복, UTC offset, DST 검사를 통과**했습니다. 파일·서비스·데이터를 변경하거나 외부에 접속하지 않았습니다. 문서의 CI 137통과·서비스 13검사·성능 수치는 **기존 기록을 검토한 것이며 이번에 재실행한 결과가 아닙니다.**

강점은 다음 세 가지입니다.

1. **데이터의 의미를 성급하게 통일하지 않습니다.** ONS의 MWmed를 kWh로 바로 바꾸지 않고, 미명시 시간대를 추측하지 않으며 verified/forecast/unspecified를 보존합니다. `ts_utc=null`도 결측 처리 실패가 아니라 명시적 계약입니다. [ons.py:164](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/acquisition/ons.py#L164), [ONS 계약:9](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/ons-source-contract.md#L9). BR-PVGen도 원본 보간·표본 수·원문 필드를 보존합니다. [parquet.py:80](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/normalize/parquet.py#L80)

2. **재실행의 성공보다 잘못된 게시를 막는 데 집중했습니다.** 기대 active 비교, PostgreSQL 잠금, metadata와 일별 결과의 동일 트랜잭션, ONS cursor 비교가 코드에 있습니다. 이는 “멱등성을 고려했다”는 문장보다 강한 증거입니다. [pipeline.py:434](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/pipeline.py#L434), [ons.py:264](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/acquisition/ons.py#L264). 동시 배치와 실패 게시 테스트도 구체적인 경쟁 순서를 만듭니다. [게시 테스트:20](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/tests/test_publication_boundaries.py#L20)

3. **측정 결과를 과장하지 않습니다.** 합성과 공개 자료, 전체 51개와 해당 월 5개, 전체 처리 이력과 최신 버전 검사, 단일 호스트 병렬 실행을 구분합니다. CPU 증가와 응답 내용 차이까지 밝힌 점은 긍정적입니다. [CASE_STUDY:32](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/portfolio/CASE_STUDY.md#L32)

채용 판단에서 확인하고 싶은 문제는 다섯 가지입니다.

| 구분 | 근거와 문제 | 평가 |
|---|---|---|
| **확인된 진단 정보 손실** | ONS는 `ONS_CURSOR_CONFLICT`, `ONS_SOURCE_CONTRACT_CHANGED`처럼 구체적인 예외를 만들지만 실패 기록에는 `type(exc).__name__`만 저장합니다. 여러 원인이 모두 `ValueError`로 남습니다. [ons.py:283](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/acquisition/ons.py#L283), [ons.py:376](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/acquisition/ons.py#L376) | CLI traceback은 남을 수 있으나 카탈로그/API만으로 원인을 구별하기 어렵습니다. 데이터 손상 결함으로 판정한 것은 아닙니다. 안전한 구조화 오류 코드가 필요합니다. |
| **확인된 운영 기능 공백** | 강제 종료 후 남은 running 상태의 자동 조정과 외부 경보가 없습니다. [CASE_STUDY:67](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/portfolio/CASE_STUDY.md#L67). 수동 `inspect-runs` 절차는 있습니다. [recovery.md:17](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/runbooks/recovery.md#L17) | 실패 게시를 막는 것과 장애를 발견·종결하는 것은 다릅니다. 로컬 시연에는 수용 가능하지만 무인 운영을 맡길 근거로는 부족합니다. |
| **선택적 확장·미검증** | `db-migrate`는 Catalog 생성 후 schema_version `"1"`을 반환하고, Catalog는 `create_all`과 특정 인덱스 생성을 수행합니다. [cli.py:204](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/cli.py#L204), [postgres.py:153](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/src/solarops/storage/postgres.py#L153) | 현재 신규 테이블 생성에는 맞지만 일반적인 버전별 스키마 변경·데이터 이행·롤백 체계의 증거는 아닙니다. 현재 데이터가 잘못됐다는 뜻은 아닙니다. |
| **성능 주장 범위의 한계** | 공개 4일, 단일 kind 호스트, 직렬 후 병렬 각 1회이며 하나의 4일 CLI 배치와 비교하지 않았습니다. [incremental-v0.5.0.md:43](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/benchmarks/incremental-v0.5.0.md#L43) | 47.3%는 해당 실험 관측값으로 인정합니다. 일반 처리량, Kubernetes의 경제성, 선형 확장성 근거로는 사용하지 않겠습니다. 현 문서는 이 한계를 제대로 밝힙니다. |
| **증거 전달의 제한** | 성능 원본·Pod 로그·자원 표본은 Git 제외 artifacts에 보존되어 있습니다. [incremental-v0.5.0.md:45](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/benchmarks/incremental-v0.5.0.md#L45). 앱 외 Airflow 전이 의존성 전체도 동일 lockfile에 고정된 것은 아닙니다. [technology-stack.md:45](https://github.com/TaeyanG4/solarops-audit/blob/66d63486722dfb7bc83418667c90db1cecfadbf6/docs/architecture/technology-stack.md#L45) | 문서와 실행 절차는 있지만 새 심사자가 같은 환경·원본 측정을 바로 검증할 수 있다는 보장은 제한적입니다. 비밀정보를 제거한 작은 측정 요약이 있으면 전달력이 좋아집니다. 전체 raw 데이터 커밋은 필요 없습니다. |

실제 면접에서는 다음 질문을 하겠습니다.

| 질문 | 좋은 답변의 필수 요소 | 경고 신호 |
|---|---|---|
| **객체 업로드 직후 프로세스가 죽거나, 이전 작업이 나중에 완료되면 무엇이 보입니까?** | 객체와 활성 카탈로그 구분, DB rollback, CAS/기대 run ID, 고아 객체, 일별·월별 원자성 차이, 실제 코드 위치 | “트랜잭션이니까 S3까지 전부 rollback됩니다.” |
| **ONS 1MWmed를 왜 곧바로 1,000kWh로 저장하지 않았습니까?** | 확인된 구간 길이·anchor·시간대 필요, 원천 분류와 중복 집계 위험, raw 보존, 향후 계약 확인 후 변환 방법 | MW와 MWh를 혼동하거나 브라질이라는 이유만으로 UTC offset을 고정 |
| **관측률 100%, 유효값 74.9%, 보간 17%가 동시에 가능한 이유는 무엇입니까?** | 분모와 자연키, 무효/누락/0 구분, 보간은 겹치는 속성, 가중 월 집계, 관측 범위 기반 기대 슬롯의 한계 | 비율을 더해 100%가 되어야 한다거나 날짜별 비율을 단순 평균 |
| **동시 2개가 47.3% 빨랐다는 결과로 무엇을 결정할 수 있습니까?** | 비교 단위, cache·기동 비용·반복 부족, CPU 24.3% 증가, 결과 hash 검증, 단일 배치 baseline과 반복 순서 교차 설계 | “Kubernetes를 쓰면 처리량이 두 배 됩니다.” |
| **ONS 실패 원인을 API에서 구분하도록 작은 변경을 해보세요.** | typed/domain error 또는 안전한 코드 매핑, 비밀정보 비노출, 이전 성공 cursor 유지, 기존 테스트 확장, 알 수 없는 예외 fallback | 예외 문자열 전체를 무조건 노출하거나 실패 때 성공 cursor를 덮어씀 |

제출 전 판단과 후속 작업은 구분하겠습니다.

- **제출을 막는 필수 기술 수정은 이번 검토에서 확인하지 못했습니다.** ONS 오류 코드 보존은 작고 효과적인 우선 개선이지만, 이를 완료하지 않았다고 신입 면접을 거절할 수준은 아닙니다. 제출 링크의 비공개 저장소 접근 권한과 합성 데모 실행 절차는 실제 제출 대상 관점에서 확인해야 합니다.
- **면접 준비가 가장 중요합니다.** 위 다섯 질문을 코드 없이 먼저 설명하고, 이어 정확한 함수와 테스트를 찾아 보여줄 수 있어야 합니다. AI가 제안한 것 중 무엇을 채택·거절했고 어떤 실패를 본인이 재현했는지 구체적인 사례 두 개를 준비하십시오. SQL 집계·window 함수, Python 디버깅과 작은 변경 구현 능력은 별도로 검증해야 합니다.
- **선택적 확장:** 스키마 migration, stale run 조정·경보, 객체 보존 정책, 반복 성능시험, 다른 호스트 복구입니다. Kafka/Spark, 고객 인증, 공개 배포를 제출 조건으로 추가할 이유는 없습니다.

이 저장소의 채용 가치는 기술 개수가 아니라 **숫자의 의미와 게시 실패를 설명할 수 있게 만든 구조**에 있습니다. 그 구조를 본인이 이해하고 수정할 수 있다는 점을 면접에서 확인한다면, 신입·주니어 후보로 충분히 긍정적으로 평가하겠습니다.
