# 개발에 사용한 AI 스킬

[프로젝트 홈](../../README.md) · [디자인 시스템](../design/overview-system.md) · [실제 UI 검증](../benchmarks/overview-redesign-20261023.md)

스킬은 구현과 검수를 돕는 개발 지침·도구입니다. SolarOps의 런타임 의존성이 아니며, 앱을 실행하는 사람은 이 스킬들을 설치할 필요가 없습니다. 아래 기록은 2026-10-23에 실제 적용한 범위입니다. GitHub 별 수나 자동 추천 점수를 품질 검증으로 사용하지 않았습니다.

| 스킬 / 공식 저장소 | 실제 사용 목적 | 적용 결과와 근거 |
|---|---|---|
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 에너지 분석 화면의 정보 위계·색·글자·차트·반응형 가이드 검색 | [전체 현황 디자인 시스템](../design/overview-system.md): KPI 요약 띠, 의미별 색, 13/14px 표, 고정 12px 축, 날짜 탐색·대체 수치표 |
| [Impeccable](https://github.com/pbakaus/impeccable) | context, craft-floor, operate, audit, polish 지침으로 가독성·상태·접근성·반응형 검수 | [발견 문제와 수정](../benchmarks/overview-redesign-20261023.md): 축소되는 축, 숨는 상세 버튼, 보간 의미, 모바일 필터 잘림 등을 보완 |
| [Agent Browser](https://github.com/vercel-labs/agent-browser) | 실제 Chrome 렌더링, 필터·키보드·실패 경로 검사, 스크린샷 | [1440/768/390px 전후 검증](../benchmarks/overview-redesign-20261023.md), [최신 README 이미지](../portfolio/images/readme-20261023/README.md) |
| [skill-installer](https://github.com/openai/skills/tree/main/skills/.system/skill-installer) | 사용자가 요청한 위 세 스킬을 공식 저장소에서 로컬 설치 | 개발 환경 준비. 앱 의존성·API·데이터 계산에는 추가하지 않음 |

## 자동 추천을 적용한 방식

UI UX Pro Max에서 `energy operations analytics dashboard`, `analytics dashboard data quality`를 검색했습니다. 자동 결과에 포함된 landing / enterprise gateway 방향은 역사 자료를 읽는 운영 화면에 맞지 않아 채택하지 않았습니다. 일반 가이드의 정보 위계·조밀한 데이터 표현·대비·키보드 접근을 사용하고, 일별 합계에는 막대 차트와 수치 탐색을 적용했습니다.

Impeccable 4.7.0의 정적 detector 결과는 최초 및 후속 검사에서 `[]`, 종료 코드 0이었습니다. 이는 코드 검출 결과이며 실제 사용성 판단을 대신하지 않습니다. 검수는 자체 평가로 기록했고 독립된 두 에이전트의 critique나 사용자 조사를 수행했다고 주장하지 않습니다.

Agent Browser CLI 0.39.1 / Headless Chrome 155 / axe-core 4.12.1로 전체 현황을 검사했습니다. 세 요구 너비에서 axe 위반 0건, 키보드 탐색·필터·빈값·오류 복구·합성 터치를 확인했습니다. 실제 스마트폰·스크린리더·다른 브라우저의 검증과는 구분합니다. README 갱신 때는 같은 CLI로 공개 2024년 4월 화면과 **합성 실패 주입** 근거를 다시 캡처했습니다.

## 코드와 증거

- 구현: [HTML](../../src/solarops/api/dashboard.html), [CSS](../../src/solarops/api/static/dashboard.css), [JavaScript](../../src/solarops/api/static/dashboard.js).
- 설계 판단: [전체 현황 디자인 시스템](../design/overview-system.md).
- 전후 이미지·검사·한계: [UI 검증 보고서](../benchmarks/overview-redesign-20261023.md).
- 적용 날짜와 후속 작업: [2026-10-23 작업 기록](../worklog/2026-10-23.md).

Web Design Guidelines와 Taste Skill은 추천 목록에만 있었으며 이번 구현에 적용하지 않았습니다. 별도 제품 의존성이나 검수 실적으로 표시하지 않습니다.

## 앞으로의 작업 기록

사용자 요청에 따라 2026-10-23부터 research-orchestrator 스킬과 discoveries 기록을 작업 절차에서 제외했습니다. 현재 상태는 [handoff](../../handoff.md), 미완료 우선순위는 [plan](../../plan.md), 상세 근거는 [날짜별 작업 기록](../worklog/README.md)에 둡니다. 이전 문서는 [보관본](../worklog/archive/README.md)으로 남기며 현재 지침으로 사용하지 않습니다.
