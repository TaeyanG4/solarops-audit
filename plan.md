## Agent: A

### H-A-06 — 승인된 고객 표본과 구매 의사 검증
- Sources: D-A-001
- Hypothesis: 국내 O&M의 반복 보고 작업 절약과 재구매로 서비스 수익성을 판정할 수 있다.
- Evidence: 실제 인터뷰·고객 파일·계약·결제 없음. 고객 연락·자료 사용의 구체 승인과 표본이 필요하여 현재 실행 의존성 미충족.
- Improvement: 공개 브라질 데이터의 기술 검증을 실제 업무 가치 검증과 분리.
- Impact: 3
- Information: 3
- Confidence: 0
- Unblock: 2
- Diversity: 2
- Cost: 3
- Priority: 16
- Resource: CPU
- Parallel: NO
- Other: NONE
- Next test: 사용자가 승인한 상대·접촉 방식·표본이 제공되면 단위/간격/시간대 매핑, 1개 유료 파일럿의 전후시간과 기여이익·재구매를 확인한다.

### H-A-11 — 잔여 계산·보고서·의존성·릴리스 감사
- Sources: D-A-008
- Hypothesis: 시계열 후보·분모 경계, 보고서 실패/동시성, 의존성·패키징을 점검하면 남은 고가치 로컬 결함을 식별할 수 있다.
- Evidence: raw/보고서 추가3실패 수정, Windows112·WSL113·서비스5 통과. 최종 이미지/DAG/CI 확인 중. 독립 리뷰 PENDING.
- Improvement: 이미 통과한 전체자료 반복 대신 아직 미검사인 실패 경계에 집중.
- Impact: 3
- Information: 3
- Confidence: 3
- Unblock: 2
- Diversity: 2
- Cost: 1
- Priority: 21
- Resource: CPU
- Parallel: NO
- Other: NONE
- Next test: 연속 후보 임계 미달과 DST/UTC그리드, 보고서 실패 원자성·동시 요청, dependency audit, CI/이미지/문서 일치를 확인하고 실제 문제만 후속 처리.
