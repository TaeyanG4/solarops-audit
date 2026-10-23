# 포트폴리오 제출 마감 검증

PORT-01~04 완료. 앱 **v0.5.1**, 구현 커밋 `ee791cbec296be9bd37c9ad9c762383ed4dcec34`, 계산 `energy-interval-v2`. [이미지 식별자](../releases/0.5.1.json) · [변경 기록](../worklog/2026-10-23-portfolio-finish.md).

## 실행한 검증

| 검사 | 결과 |
|---|---|
| 로컬 오프라인 | 136통과·14제외,46.33초. 호스트의 symlink 생성 불가1개와 opt-in 서비스13개 제외 |
| 새 checkout CI | [39915517455](https://github.com/TaeyanG4/solarops-audit/actions/runs/39915517455) Windows/Ubuntu 각각137통과·13제외. Ruff·JS·문서·릴리스·합성데모·복원·wheel/소스 패키지 성공 |
| 신규 상태 API | 기존 ONS 검사2개 확장: 실패 후 cursor 보존, 최근20회 모두 실패여도 성공 확인, 다른 조직의 월/성공 누출 방지. 새 테스트 함수 없음 |
| 실제 저장소 조회 | Compose PostgreSQL/MinIO의10월 69,696 PV행·21일, 변경0일. 스케줄러 상태는 not_observed이며 다른 환경과 혼합하지 않음 |
| 기존 공개 응답 | overview 2024-04·public와 report 목록의 배포 전후 응답 SHA 동일. 모든 API를 전수 비교한 것은 아님 |
| DAG/배포 | local/Kubernetes 모드 각각7DAG import·template 성공. Compose dashboard/중지된 Airflow3개와 kind Airflow/KPO 선언0.5.1 정렬. kind6개 서비스 Pod Ready |
| 일정 보존 | 16:09 KST kind ONS만 활성·나머지6개 paused·running/queued0. 이번 릴리스에서 새 ONS 정기 실행까지 기다린 것은 아님 |
| 실제 화면 | Agent Browser Chromium1440×1000,768×1024,390×844. 월 키보드 선택·URL복원·일별 펼치기·빈 월·통신 실패·재시도·합성 데모 조회 |
| 접근성/가독성 | 세 너비 axe4.12.1 각0위반, 열린 일별 내역0위반.390px 가로 넘침0·본문/레이블14px미만0. 닫힌 popover aria-controls1개는 자동판정 incomplete; 실제 선택/키보드 동작 확인 |

기존 실제 PostgreSQL/MinIO13검사와 공개 정기 KPO/병렬 측정은 [v0.5.0](incremental-v0.5.0.md)의 역사 근거입니다. 이번에는 그 전체 부하를 재실행하지 않았습니다.

## 화면 변경과 검수

데이터 출처 안에 **BR-PVGen 역사 분석 / ONS 수집 상태**를 분리했습니다. ONS 월은 기존 보고 월과 별개로 주소에 저장합니다. 최근 시도와 마지막 성공, 변경 날짜를 구분하고 성공 없는 월·실패 후 성공 보존·실행 중 기록을 명시합니다. 원천 MWmed·미명시 시간대·예측 유형은 기존 에너지와 섞지 않습니다.

UI UX Pro Max의 오류·빈 상태·반응형 가이드를 적용했고, Impeccable context/craft-floor/audit와 정적 detector(0건)를 사용했습니다. 첫 브라우저 확인에서 발견한 정의 목록의 잘못된 p 위치와390px 버튼 줄바꿈을 수정한 후 검사했습니다.

| Impeccable 검수 축 | 평가 /4 | 근거·제한 |
|---|---|---|
| 접근성 | 3 | 세 너비 axe0, 키보드 월 선택. 스크린리더/실제 기기 미검증 |
| 성능 | 3 | ONS 상태1요청·최근20시도·월별 일목록, 프런트엔드 의존성 추가 없음. 새 부하 측정 없음 |
| 토큰 일치 | 3 | 기존 색·글꼴·16/14px·공통 선택창 유지. 별도 dark mode 없음 |
| 반응형 | 3 | 세 너비·줄바꿈·가로 넘침·펼친 일별 내역 확인. 실제 터치 기기 미검증 |
| 구현/표현 정합성 | 4 | 실제 API 값·환경·미수집/실패/보존 구분, 원문 단위와 출처 유지 |

16/20은 이번 ONS 추가 화면의 제한된 검수 평가이며 인증/보안 인증이나 서비스 준비도 점수가 아닙니다. [전후·세 너비 이미지](../portfolio/images/portfolio-finish-20261023/README.md).

실패 후 성공 보존 UI는 브라우저 응답 모의로 확인했습니다. 실제 Compose 수집 실패를 발생시키거나 실제 이력을 바꾸지 않았습니다. 모의 화면은 실수집 실적으로 사용하지 않으며 Git에는 정상 실제 자료 화면만 게시했습니다.

## 문서 명령으로 최종 재현

`uv sync --frozen` 후 `uv run python scripts/demo/portfolio_demo.py --output artifacts/portfolio-final-demo --serve --port 8503`을1회 실행했습니다. 새 폴더의 SQLite·파일만 사용했고 원본 다운로드·기존 DB 의존 없이 합성7일 처리 → 커밋 실패 → 이전 성공 보존 → 동일hash 재처리 → 보고서를 확인했습니다.

- 활성7일, 완료batch2·실패batch1, `failed_publish_kept_active_data=true`, `replay_hashes_identical=true`.
- 실제 보고서 `09c45c95-940f-46b5-b28e-f8edd8dfbf79` 조회, Ctrl+C 후 graceful shutdown와8503포트 종료 확인. 증거 파일은 보존.
- 실패 상세 캡처와 ONS 없는 환경 확인은 같은 산출물을 읽는8506서버로 추가 조회했습니다. 처리 데모를 재실행하지 않았고8506도 종료했습니다.
- 로컬 원본 증거 SHA-256: `cf9e033bd659a72c05e1ba47ab702a384f0d390919f46afde84d787b3dde9d5c`. [공유 가능한 요약](portfolio-finish-20261023.json).

## 제출 범위

[한 쪽 요약](../portfolio/SUBMISSION.md) · [3~5분 시연](../portfolio/DEMO_GUIDE.md) · [설계 질문5개와 코드](../portfolio/DESIGN_QUESTIONS.md) · [최신 README](../../README.md)를 연결했습니다.

계획의 네 항목을 모두 완료했다는 의미에서 제출 범위100%입니다. 무결점·합격·지원자 설명 숙련도·상용 운영을 보증하지 않습니다. 영업BIZ-01은 사용자 요청대로 후순위이며 고객 인증·공개 배포·Kafka/Spark는 마감 필수 범위가 아닙니다.
