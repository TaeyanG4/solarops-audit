## Agent: A

### H-A-02 — v2 공개 자료 비교와 서비스 전환
- Sources: D-A-002, D-A-007
- Hypothesis: v2를 별도 계산 버전으로 적재하고 구버전과 비교한 뒤 화면을 전환하면 기존 결과 보존과 수정 배포를 함께 충족한다.
- Evidence: D-A-007의 전체 비교·배포·기능26fdaef CI 성공. 후속18cdf64 CI39794977186의 최종 결과 대기; 자료 재처리는 필요 없음.
- Improvement: 새 버전의 전체 공개 일별 지표 비교와 null 시계열 확인, 이미지/보고서 전환, CI 성공까지 기록.
- Impact: 3
- Information: 3
- Confidence: 3
- Unblock: 3
- Diversity: 1
- Cost: 0
- Priority: 22
- Resource: CPU
- Parallel: NO
- Other: NONE
- Next test: 후속18cdf64 CI39794977186 완료 결과 확인. 실패면 해당 실패만 수정·검증, 성공이면 근거 기록 후 H-A-02를 완료 로그로 이동. 이미 통과한 전체 자료/배포 검증을 반복하지 않는다.

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
