## Agent: A

### H-A-02 — v2 공개 자료 비교와 서비스 전환
- Sources: D-A-001, D-A-002
- Hypothesis: v2를 별도 계산 버전으로 적재하고 구버전과 비교한 뒤 화면을 전환하면 기존 결과 보존과 수정 배포를 함께 충족한다.
- Evidence: D-A-002의 회귀 통과로 선행조건 충족. D-A-001/002 모두 독립 교차 검증 PENDING. 실제 v1 공개 파티션12,572개 기준을 별도 보존함.
- Improvement: 새 버전의 전체 공개 일별 지표 비교와 null 시계열 확인, 이미지/보고서 전환, CI 성공까지 기록.
- Impact: 3
- Information: 3
- Confidence: 3
- Unblock: 3
- Diversity: 1
- Cost: 2
- Priority: 20
- Resource: CPU
- Parallel: NO
- Other: NONE
- Next test: v1 기준 목록 보존 → 51개 서비스 재처리 → 일별 에너지·품질 대조 → v2 보고서·Compose/kind 검증. 기존 원본·v1·볼륨은 삭제하지 않는다.

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
