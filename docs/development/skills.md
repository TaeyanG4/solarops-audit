# 개발에 사용한 AI 스킬

## 기간·보고서·진단 보완 — 2026-10-23

- UI UX Pro Max: `empty state recovery clear action labels --domain ux -n 3`의 레이블·빈 화면·복구 지침을 실제 등록/발행 월 안내에 적용했습니다. 기존 디자인과 사용자의 작업형 문구를 유지했습니다.
- Agent Browser: 기간 선택·보고서 메타데이터·실패 진단에서 현재 결과 이동을1440/768/390px로 확인했습니다. 모바일 axe3회 위반0, 실제 DPR2캡처를 보존했습니다.
- 새 스킬 설치나 별도 검수 에이전트는 사용하지 않았습니다. [실제 변경·검사·이미지](../worklog/2026-10-23-usability.md)에 범위를 기록합니다.

## 실행 이력 탐색 보완 — 2026-10-23

- UI UX Pro Max의 `filter URL state keyboard navigation --domain ux -n 3` 검색을 주소 복원·키보드 조회·보이는 레이블에 적용했습니다.
- Impeccable의 harden/craft-floor 지침으로 빈 결과·잘못된 주소·조회 범위 설명을 점검하고 세 너비 캡처를 검토했습니다. 이 범위에서 별도 에이전트 검수나 detector를 새로 실행한 것으로 기록하지 않습니다.
- Agent Browser로 발전소/상태·새로고침·뒤로/앞으로·상하위 링크·1440/768/390px를 확인했습니다. 기존 관련 테스트 5개와 단발성 브라우저 확인을 사용했으며 영구 테스트·검사 스크립트는 추가하지 않았습니다. [실제 결과·이미지·한계](../worklog/2026-10-23-run-navigation.md).

## 현재 워크스페이스에 적용한 목적

최신 근거는 [사이드바·보고서·관리 검증](../benchmarks/workspace-20261023.md), [실제 캡처](../portfolio/images/workspace-20261023/README.md), [현재 DESIGN.md](../../DESIGN.md)입니다. 아래 초기 개선과 수평 Energy Desk 기록은 단계별 이력이며 최신 화면과 구분합니다.

| 스킬 | 이번 실제 역할 | 적용/제외 판단 |
|---|---|---|
| UI UX Pro Max | `operations dashboard navigation --design-system`, `navigation hierarchy sidebar --domain ux` 검색 | 기능 위계·작업 그룹·레이블·접근성 참고. landing hero/CTA와 Fira 추천은 한국어 운영 앱에 맞지 않아 제외 |
| Impeccable4.7.0 | new-work/craft-floor/audit/polish, detector1회, 별도 finish reviewer, DESIGN/sidecar documenter | 사용자 지정 사이드바·큰 글씨·통합 보고서를 기준으로 검수. 이전 중간안 ship을 재사용하지 않음 |
| Agent Browser0.39.1 | Chrome156/axe4.12.1 실제3너비·키보드·보고서·관리 시작/중지·DPR2캡처 | overview107명령, workspace195명령, axe3+23회 위반0. 실제 기기·스크린리더 평가와 구분 |
| Web Design Guidelines | href·깊은 링크·보이는 레이블·포커스·폼·넘침 확인 | 최신 규칙 원문을 로컬 증거에 보존. 자동 점수로 사용성을 보증하지 않음 |

모든 이미지는 실제 렌더링이며 생성형 이미지 스킬은 사용하지 않았습니다. favicon은 기존 브랜드 기하를 SVG로 작성했습니다. 문서 작성에는 research-orchestrator를 사용하지 않고 짧은 handoff·우선순위 plan·날짜별 수행 기록을 유지했습니다. 설치 명령과 버전은 아래에 보존합니다.

이번 detector64항목은 이전 DESIGN과 달라진 토큰 advisory63개와 admin의 정적 stylesheet 경로 해석으로 인한 글자 위계 경고1개입니다. 실제 캡처/계산 스타일과 별도 검수를 함께 확인했습니다. 초기 detector0건과 혼동하지 않습니다. 원본 evidence는 `artifacts/ui-workspace-20261023/`에 있습니다.

## 초기 개선의 이력

[프로젝트 홈](../../README.md) · [디자인 시스템](../design/overview-system.md) · [실제 UI 검증](../benchmarks/overview-redesign-20261023.md)

스킬은 구현과 검수를 돕는 개발 지침·도구입니다. SolarOps의 런타임 의존성이 아니며, 앱을 실행하는 사람은 이 스킬들을 설치할 필요가 없습니다. 아래 기록은 2026-10-23에 실제 적용한 범위입니다. GitHub 별 수나 자동 추천 점수를 품질 검증으로 사용하지 않았습니다.

| 스킬 / 공식 저장소 | 실제 사용 목적 | 적용 결과와 근거 |
|---|---|---|
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 에너지 분석 화면의 정보 위계·색·글자·차트·반응형 가이드 검색 | [전체 현황 디자인 시스템](../design/overview-system.md): KPI 요약 띠, 의미별 색, 13/14px 표, 고정 12px 축, 날짜 탐색·대체 수치표 |
| [Impeccable](https://github.com/pbakaus/impeccable) | context, craft-floor, operate, audit, polish 지침으로 가독성·상태·접근성·반응형 검수 | [발견 문제와 수정](../benchmarks/overview-redesign-20261023.md): 축소되는 축, 숨는 상세 버튼, 보간 의미, 모바일 필터 잘림 등을 보완 |
| [Agent Browser](https://github.com/vercel-labs/agent-browser) | 실제 Chrome 렌더링, 필터·키보드·실패 경로 검사, 스크린샷 | [1440/768/390px 전후 검증](../benchmarks/overview-redesign-20261023.md), [최신 README 이미지](../portfolio/images/readme-hidpi-20261023/README.md) |
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

Web Design Guidelines는 후속 Energy Desk 작업에서 실제 적용했습니다. Taste Skill은 사용하지 않았습니다.

## 앞으로의 작업 기록

사용자 요청에 따라 2026-10-23부터 research-orchestrator 스킬과 discoveries 기록을 작업 절차에서 제외했습니다. 현재 상태는 [handoff](../../handoff.md), 미완료 우선순위는 [plan](../../plan.md), 상세 근거는 [날짜별 작업 기록](../worklog/README.md)에 둡니다. 이전 문서는 [보관본](../worklog/archive/README.md)으로 남기며 현재 지침으로 사용하지 않습니다.

## Energy Desk 신규 디자인 및 프로젝트 설치

사용자가 기존 화면과 닮은 중간안을 거절하고 새 디자인을 요청해, HTML/CSS의 화면 구조를 다시 작성했습니다. [새 검증](../benchmarks/energy-desk-20261023.md)과 [디자인 시스템](../../DESIGN.md)이 현재 근거입니다. 위의 Chrome 155 결과는 이전 작업 기록이며, 이번 실행은 **Agent Browser 0.39.1 / Chrome 156 / axe 4.12.1**입니다.

| 스킬 | 이번 사용 |
|---|---|
| UI UX Pro Max | `data dense dashboard`의 정확한 스타일 결과, energy 색·chart 검색. fitness·radar 등 부적합한 결과를 버리고 운영 분석의 정보 위계·접근 가능한 수치표를 채택 |
| Impeccable | new-work의 신규 외형, layout의 읽기 순서·그룹 구성, craft-floor·audit·polish, 실제 캡처 기반 별도 finish review와 시스템 기록 |
| Agent Browser | 1440/768/390px 실제 Chrome, 키보드·필터·뒤로 가기·null/0·오류 복구·합성 터치, DPR2 원본 캡처 |
| [Web Design Guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | 최신 규칙 원문을 가져와 href 탐색·URL 상태·form labels·focus·반응형·theme-color 검토 |
| skill-installer | 공식 설치 경로 확인. 프로젝트 설치는 아래 공식 CLI를 사용 |

실제로 실행한 설치 명령 (저장소 루트, Windows는 `npx.cmd` / `npm.cmd`):

```text
npx --yes ui-ux-pro-max-cli@2.15.0 init --ai codex
npx --yes impeccable@4.7.0 install --providers=codex --scope=project
npx --yes skills@1.7.4 add vercel-labs/agent-browser --skill agent-browser -a codex --yes
npm install -g agent-browser@0.39.1
agent-browser install
npx --yes skills@1.7.4 add vercel-labs/agent-skills --skill web-design-guidelines -a codex --yes
```

설치 결과는 `.agents/skills/`와 로컬 `.codex/hooks.json`에 있습니다. 이 도구 파일·실행 바이너리는 Git과 Docker context에서 제외하고 [skills-lock.json](../../skills-lock.json)에 두 Vercel 스킬의 source/hash를 남겼습니다. 다른 CLI 버전은 이 문서에 고정했습니다. 브라우저 설치는 당시 Chrome 156을 받았으며 앱 런타임에 추가하지 않았습니다. AGENTS.md는 설치 전후 SHA-256이 일치합니다.

새 디자인은 사용자가 자율 구현과 이후 수정을 맡긴 code-led 작업입니다. 별도 concept-seed 선택·승인 이미지 비교를 수행한 것으로 기록하지 않습니다. Impeccable의 별도 리뷰는 코드와 제공한 캡처에 대한 검수이며 실제 고객 평가가 아닙니다.

## 선택창·관리 탭·관측 차트 후속 수정

2026-10-23 UI-04에서는 UI UX Pro Max의 dropdown/scroll/keyboard·missing/time series 검색을 적용했습니다. Impeccable의 harden·craft-floor·polish로 상호작용과 실제 캡처를 자체 검수하고, Web Design Guidelines로 직접 링크·탭 URL·포커스·키보드 스크롤을 확인했습니다. 별도 에이전트 리뷰는 수행하지 않았습니다.

Agent Browser 회귀는 1440/768/390px, 303명령·axe18회 위반0입니다. Impeccable detector는 27건(권고26·경고1)이었으며 정적 HTML의 CSS 경로를 해석하지 못한 제목 크기 경고는 실제 computed style과 대조했습니다. 이전 작업의 detector 결과를 이번 결과로 재사용하지 않습니다. [수정·검수·한계](../benchmarks/interactions-20261023.md) · [실제 캡처 출처](../portfolio/images/interactions-20261023/README.md).

UI-05에서는 사용자가 스크롤 닫힘을 거절해 열림 유지로 재수정했습니다. UI UX Pro Max의 키보드·포커스 가이드와 Impeccable harden·craft-floor의 상태·경계 검수를 적용했고, Agent Browser269명령·3너비·열린 목록 axe6회 위반0을 확인했습니다. controls.js만 검사한 detector는 `[]`입니다. [기준 구현 실패 → 수정 후 통과와 한계](../benchmarks/select-anchor-20261023.md). Web Design Guidelines는 이번 좁은 수정에서 재실행하지 않았습니다.

## 보고서 게시 근거 비교

2026-10-23 TECH-02에서는 UI UX Pro Max의 `live status screen reader` 검색에서 contextual live badge 지침을 확인해, 색과16px 문구·비교 기준 시각을 함께 표시하고 하나의 atomic status 영역을 사용했습니다. 최초 `status feedback stale data` 검색은 부적합한 결과라 적용하지 않았습니다. 기존 DESIGN.md의 색·타이포그래피를 유지했습니다.

Agent Browser로 실제 공개 자료의 동일 상태와 별도 합성 재처리의 변경 상태를 열었습니다.1440/768/390px의 넘침0, 최종 모바일 두 상태의 보고서 영역 axe 위반0·JS오류0을 확인했습니다. DPR2 원본 [화면과 출처](../portfolio/images/technical-20261023/README.md)를 보존했습니다. 백엔드·CI·복원 작업에는 UI 스킬을 적용하지 않았고, 이번 좁은 변경에서 Impeccable/Web Design Guidelines·별도 에이전트 검수를 수행한 것으로 기록하지 않습니다.

## ONS 출처 계약 확인

2026-10-23 DATA-03에서는 `pdf:pdf` 스킬로 ONS 공식 데이터 사전 PDF의 필드·단위·null/음수 규칙을 확인했습니다. 시간대나 구간 기준이 없다는 한계를 계약에 남겼습니다. UI 변경은 없으므로 디자인/브라우저 스킬을 재사용한 것으로 기록하지 않습니다. [출처 계약](../ons-source-contract.md) · [수행 기록](../worklog/2026-10-23-incremental.md).

## 2026-10-23 제출 마감의 실제 사용

- **UI UX Pro Max:** 기존 Energy Desk를 유지하고 수집 상태의 오류·빈 상태·출처·반응형 가이드를 검색했습니다. 새 시각 방향이나 프레임워크를 도입하지 않았습니다.
- **Impeccable:** context로 PRODUCT/DESIGN을 읽고 Operate 화면의 craft-floor·audit를 적용했습니다. 정적 detector 0건, 렌더링에서 정의 목록 구조·모바일 버튼 줄바꿈을 찾아 수정했습니다.
- **Agent Browser:** 실제 Compose 조회를1440/768/390px에서 확인하고 월 선택·일별 내역·빈 월·통신 실패·이전 성공 보존(브라우저 응답 모의)을 점검했습니다. [최종 근거](../benchmarks/portfolio-finish-20261023.md).
- Web Design Guidelines와 연구 스킬은 이번 작업에서 실행하지 않았습니다. 과거 사용 기록과 구분합니다.

## 2026-10-23 산출물 R1 피드백

Agent Browser로 격리 합성 보고서의 모두 불명·혼합·모두 False를1440/390/768px에서 확인했습니다. 표시·넘침·페이지 오류만 검사했고 새 디자인이나 전체 접근성 검수로 주장하지 않습니다. [변경·증거](../benchmarks/quality-v0.5.3.md). 백엔드 경계와 빌드 입력 수정에는 연구/디자인 스킬을 사용하지 않았습니다.
