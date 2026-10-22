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

### H-A-12 — 전체 현황 디자인 시스템과 구현
- Sources: D-A-011
- Hypothesis: 정보 위계·차트 탐색·품질 분리·모바일 테이블을 재설계하면 기존 수치 계약을 보존하며 현황 해석과 검토 경로가 명확해진다.
- Evidence: 사용자 명시 리디자인 요청. 기존 표10/12px, 차트 title 툴팁, 모바일 가독성은 실제 화면 기준 검증 필요. 기존 기능 D-A-011 자체검증, 독립 리뷰 PENDING.
- Improvement: 전체 현황부터 요청한 스킬 기반 설계와 1440/768/390px 전후 실측·상호작용 검증을 추가.
- Impact: 3
- Information: 3
- Confidence: 3
- Unblock: 3
- Diversity: 3
- Cost: 3
- Priority: 21
- Resource: CPU
- Parallel: NO
- Other: NONE
- Next test: 로컬 UI·Impeccable·세 viewport·API 응답 일치·Windows112/6skip 검증 완료. 기능커밋 CI와 최종 문서 인계 확인. docs/benchmarks/overview-redesign-20261023.md 참조.
