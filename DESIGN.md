---
name: "SolarOps Audit — Energy Desk Workspace"
description: "그룹별 사이드바, 읽기 쉬운 분석·보고서, 독립 로컬 관리의 실제 디자인 시스템"
colors:
  ink: "#172131"
  muted: "#59667a"
  paper: "#f1f3f7"
  surface: "#ffffff"
  subtle: "#f6f7fa"
  line: "#dce2eb"
  control-line: "#8491a5"
  nav-text: "#c0cbdc"
  nav-active: "#34445c"
  nav-hover: "#26354c"
  energy: "#f3ba55"
  energy-active: "#ffe0a1"
  accent: "#3455ba"
  focus: "#285bdd"
  green: "#16745e"
  green-dark: "#105443"
  green-soft: "#e5f2ec"
  amber: "#965d12"
  amber-soft: "#fff2d9"
  red: "#ac413d"
  red-soft: "#fff0ee"
  missing: "#67778e"
  interpolation: "#65518c"
  option-hover: "#e7edf9"
  option-text: "#243f92"
typography:
  display:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "50px"
    fontWeight: 620
    lineHeight: 1.15
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "38px"
    fontWeight: 750
    lineHeight: 1.2
    letterSpacing: "-0.04em"
  quality:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "46px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.04em"
  title:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "19px"
    fontWeight: 700
    lineHeight: 1.55
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  control:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.55
  report-body:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
  report-energy:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "42px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.03em"
  report-title:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "23px"
    fontWeight: 700
    lineHeight: 1.35
  report-table:
    fontFamily: "Pretendard, \"Segoe UI\", \"Malgun Gothic\", sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.65
  code:
    fontFamily: "Consolas, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.8
rounded:
  meter: "2px"
  badge: "4px"
  option: "6px"
  control: "8px"
  popover: "10px"
  card: "12px"
  panel: "14px"
spacing:
  compact: "8px"
  small: "12px"
  field: "16px"
  mobile: "20px"
  section: "24px"
  panel: "28px"
  page: "32px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
  input-search:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
    width: "205px"
  navigation:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.nav-text}"
    padding: "28px 16px 20px"
    width: "224px"
  chip-status:
    backgroundColor: "{colors.green-soft}"
    textColor: "{colors.green-dark}"
    rounded: "{rounded.badge}"
    padding: "3px 8px"
  card-quality:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "28px"
  select-trigger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  month-dialog:
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "28px"
    width: "100%"
  report-band:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "32px"
  service-row:
    textColor: "{colors.ink}"
    padding: "22px 0"
---

# Design System: SolarOps Audit — Energy Desk Workspace

## Overview

**Creative North Star: "Energy Desk"**

Energy Desk는 역사 자료를 읽고 다음 검토 대상을 고르는 작업 책상입니다. 차가운 종이색 바탕, 짙은 잉크색 분석 공간, 에너지를 표시하는 금색이 수치의 위계를 만듭니다. 로컬 Pretendard와 폭을 맞춘 숫자, 간결한 구분선이 정보가 많은 화면의 읽기 속도를 지탱합니다.

그룹별 사이드바는 분석·감사 자료·관리를 구분합니다. 본문과 보조 글씨의 가독성, 키보드로 조작하는 선택창, 메인 문서에 이어지는 월간 보고서가 공유 원칙입니다. 독립 관리 화면은 같은 시각 언어로 서비스 상태와 시작·중지의 영향을 설명합니다.

사용자가 확정한 사이드바·글씨 크기·선택창·통합 보고서 요구를 실제 코드에서 추출했습니다. 수평 탐색은 이전 중간안입니다. 새 시안 추첨, 이미지 comp 또는 시안 일치 점수를 근거로 삼지 않습니다.

**Key Characteristics:**

- 분석·감사 자료·관리로 묶은 일곱 목적지와 명확한 현재 위치.
- 잉크·금색 에너지 영역, 흰 품질 면, 차가운 종이색 배경.
- 본문 16px와 화면 보조 글씨 최소 14px, 로컬 한글 글꼴과 고정폭 숫자.
- 보이는 레이블과 키보드 탐색을 갖춘 월·목록 선택창.
- 한 문서의 보고서 흐름과 별도 로컬 관리 화면.
- 추정치·자료 출처·품질 분류·원본 보간을 구별하는 데이터 표현.

이 문서는 2026-10-23의 [대시보드 HTML](src/solarops/api/dashboard.html), [공유 CSS](src/solarops/api/static/dashboard.css), [선택창](src/solarops/api/static/controls.js), [탐색](src/solarops/api/static/navigation.js), [화면 구성](src/solarops/api/static/dashboard.js), [관리 HTML](src/solarops/admin/index.html)·[동작](src/solarops/api/static/admin.js), [보고서 CSS](src/solarops/api/static/report.css)·[인쇄 템플릿](src/solarops/reports/templates/monthly.html)을 기준으로 합니다. 제품 제약은 [PRODUCT.md](PRODUCT.md), 방향과 최종 추가 요건은 [워크스페이스 계약](docs/design/workspace-navigation.md)에 있습니다.

기존 [실행 검증](docs/benchmarks/workspace-20261023.md)은 워크스페이스 195명령·23회 axe 위반 0, 별도 수명주기 132명령을 기록합니다. 최신 별도 검수의 `ship`은 제공 캡처와 샘플 소스에 대한 UI 판정입니다. 이 문서화에서는 소스와 대표 캡처를 읽고 YAML/JSON 구조·토큰 참조를 확인했으며, 브라우저·접근성·서비스 수명주기를 재실행하지 않았습니다. 실제 기기·스크린리더·다른 브라우저·인쇄 PDF 페이지 나눔과 고객 성과는 검증 범위 밖입니다.

## Colors

금색은 에너지, 파란색은 행동, 녹색·황토색·회청색은 데이터 품질에 배정합니다. 정확한 값은 frontmatter가 기준입니다. CSS의 `--nav`는 `ink`와 같고, 보고서의 `--report-ink/muted/line/gold`는 각각 `ink/muted/line/energy`와 같습니다.

### Primary

- **짙은 잉크 (`ink`)**: 사이드바·분석·보고서 합계 면, 기본 버튼과 밝은 면의 본문색입니다.
- **태양 금색 (`energy`, `energy-active`)**: 추정 에너지, 일별 막대, 현재 탐색 아이콘, 어두운 면의 포커스를 표시합니다. 밝은 변형은 선택한 막대입니다.

### Secondary

- **작업 파랑 (`accent`, `focus`)**: 링크와 밝은 면의 포커스입니다. **목록 파랑 (`option-hover`, `option-text`)**은 선택창에서 탐색 중인 항목을 구별합니다.
- **유효 녹색 (`green`, `green-dark`, `green-soft`)**: 유효 슬롯·비율과 완료 배지입니다.
- **무효 황토색 (`amber`, `amber-soft`)**: 무효값·부분 기간과 검증 완료 배지입니다. 설비 고장을 뜻하지 않습니다.
- **오류 적색 (`red`, `red-soft`)**: 실패 상태와 관리 오류 메시지입니다.
- **누락 회청색 (`missing`)**: 누락 슬롯입니다. **보간 보라색 (`interpolation`)**은 중첩 가능한 원본 보간 속성입니다.

### Neutral

- **차가운 종이 (`paper`)**, **흰 면 (`surface`)**, **얕은 회색 (`subtle`)**: 바탕, 패널·조작부, 표 머리글·보조 영역을 구분합니다.
- **설명 회색 (`muted`)**, **분리선 (`line`)**, **조작부 경계 (`control-line`)**: 본문 보조 정보와 서로 다른 강도의 경계입니다.
- **탐색 회청색 (`nav-text`)**, **선택 잉크 (`nav-active`)**, **탐색 잉크 (`nav-hover`)**: 사이드바 설명, 현재 위치, hover입니다.

**The Semantic Color Rule.** 에너지, 행동, 유효·무효·누락, 원본 보간의 색 역할을 섞지 않고 문자와 도형으로 의미를 함께 전달합니다. 서비스 실행·건강·준비 상태는 해당 문맥의 문자로 구별합니다.

어두운 차트 면은 지역 변수로 설명·경계·누락·포커스의 대비를 조정합니다. 사이드카의 8단계 OKLCH tonal ramp는 계산한 팔레트 탐색 견본이며 앱 상태색이나 대비 검증 결과가 아닙니다.

## Typography

**Display Font:** Pretendard Variable 1.3.9, 로컬 WOFF2. 대체 글꼴은 Segoe UI, Malgun Gothic, sans-serif입니다.

**Body Font:** 같은 스택입니다. 앱은 preload와 `font-display: swap`을 사용합니다. 독립 보고서는 글꼴과 [OFL 라이선스](src/solarops/api/static/fonts/OFL.txt)를 자체 포함합니다.

**Label/Mono Font:** 레이블은 Pretendard, 실행 계보 코드 블록은 frontmatter의 `code`입니다.

### Hierarchy

- **Display / Quality**: 추정 발전량과 유효값 비율은 각각 `display`·`quality`입니다. 에너지는 900px 이하 48px, 600px 이하 42px; 품질은 600px 이하 42px입니다. 에너지 단위는 15px/450입니다.
- **Headline / Title**: 페이지 제목은 `headline`, 패널 제목은 `title`입니다. 페이지 제목은 901–1220px에서 32px, 900px 이하 34px, 600px 이하 32px입니다. 일반 패널 제목은 600px 이하 18px입니다.
- **Body / Label / Control**: `body`·`label`·`control`을 사용합니다. 기본 버튼은 본문 크기와 굵기 600, 목록 trigger와 월 trigger는 `control`, 600px 이하에서는 16px입니다. 표·범례·출처·상태 배지는 최소 글씨 규격을 사용합니다.
- **Report**: `report-body`의 넉넉한 줄높이, `report-energy`의 합계, `report-table`의 수치를 사용합니다. 보고서 합계는 600px 이하 34px, 품질 지표는 기본 30px에서 26px로 줄어듭니다. 통합 보고서 띠의 제목은 30px에서 26px로 줄어듭니다.
- **Report section titles**: 독립 HTML의 h2는 `report-title`입니다. 앱은 report.css 다음 dashboard.css를 로드하므로 보고서 패널 h2에도 일반 패널의 19px/18px와 굵기 700이 적용되고, 줄높이는 보고서의 1.35를 유지합니다. 독립 HTML의 상단 제목은 별도의 h1입니다.
- **Print**: 보고서 본문은 11pt, 표는 9pt입니다. 화면의 최소 글씨 규격과 인쇄 매체 규격을 혼동하지 않습니다.

**The Readable Text Rule.** 화면 본문은 16px, 표·범례·레이블·설명·조작 글씨는 최소 14px를 유지합니다. 인쇄 매체의 pt 규격은 별도로 적용합니다.

**The Numeric Reading Rule.** 에너지·품질·발전소 수·표의 숫자는 `tabular-nums`로 정렬하고 단위와 추정 여부를 가까이 둡니다.

## Layout

데스크톱은 고정 사이드바와 오른쪽 문서 영역입니다. 사이드바 폭은 frontmatter의 `navigation.width`, 안쪽 여백은 같은 컴포넌트 규격입니다. 본문은 왼쪽 여백 224px, 최대 너비 1760px, 좌우 32px입니다. 조회 띠 최소 높이는 100px이고 본문 시작은 32px입니다. 제목 설명은 최대 70ch, 일반 정의 목록 설명은 75ch입니다.

전체 현황의 분석 열은 `minmax(0, 1.65fr) minmax(300px, 1fr)`입니다. 간격은 기본 24px, 1150px 이하 20px입니다. 보고서 요약·증거 영역은 2열, 품질 정의 목록은 4열을 사용합니다. 다른 기능에 동일한 열 비율을 강제하지 않습니다.

| CSS 조건 | 실제 변화 |
|---|---|
| 901–1220px | 본문 좌우 24px, 조회 띠·제목 줄바꿈, 전체 현황 분석 1열 |
| 1150px 이하 | 일반 패널 여백 24px, 조작부 간격 축소; 이후 더 구체적인 규칙이 우선 |
| 900px 이하 | 사이드바가 문서 흐름의 헤더로 전환, 메뉴 열기로 세 그룹을 3열 표시; 본문 왼쪽 여백 0·좌우 28px; 보고서 띠·증거 1열, 지표 2열 |
| 600px 이하 | 본문 좌우 20px, 열린 탐색 1열; 월·새로고침 다음 줄에 자료 구분; 품질·출처·보고서 일별 표를 레이블 있는 기록으로 표시 |

발전소 표는 900px 이하에서 2열 기록 묶음, 600px 이하에서 한 발전소씩 배치합니다. 품질·출처·보고서 일별 내역은 작은 화면에서 한 기록 안의 수치 2열을 유지합니다. 관리 컨테이너 표는 600px 이하 세로 레이블 목록입니다. 가로로 긴 표는 가로 탐색을 허용합니다.

통합 보고서는 메인 DOM의 article이며 페이지 전체의 세로 스크롤을 공유합니다. 일별 내역은 details로 펼칩니다. 독립 인쇄 HTML은 최대 너비 1260px와 좌우 32px, 600px 이하 20px 여백을 사용합니다. 인쇄에서는 외곽 여백을 제거하고 표 머리글 반복·행 나눔 방지·실제 배경색 출력을 지정합니다. 실제 PDF 페이지 나눔 검증을 뜻하지 않습니다.

## Elevation & Depth

내용 패널은 종이색·흰색·잉크색 면과 1px 구분선으로 나눕니다. 선택창만 다른 내용 위에 놓이는 관계를 그림자로 설명합니다. 월 선택과 관리 확인 dialog는 반투명 배경으로 작업 범위를 구분합니다.

### Shadow Vocabulary

- **목록 선택창** (`0 12px 28px rgb(23 33 49 / 16%)`): 고정 위치 popover의 경계입니다.
- **모달 배경** (`rgb(12 20 33 / 55%)`): 그림자가 아닌 `::backdrop`입니다. dialog 자체에는 명시적인 box-shadow가 없습니다.

**The Functional Depth Rule.** 내용 면은 명도와 구분선으로 나누고, 그림자는 열려 있는 목록 선택창의 겹침을 설명하는 데 사용합니다. 장식적인 떠오름을 추가하지 않습니다.

## Shapes

큰 패널·dialog는 `panel`, 요약 카드는 `card`, 입력·버튼·탐색 항목은 `control`, 목록 팝업은 `popover`, 목록 항목은 `option`, 상태 배지는 `badge` 모서리를 사용합니다. 대부분 조작부는 최소 높이 44px, 사이드바 링크는 46px입니다. 포커스는 3px 외곽선과 4px 간격, 어두운 탐색·분석 영역에서는 금색입니다.

유효값 원·무효값 사각형·누락 점선 사각형은 품질색을 보완합니다. 차트는 막대·미등록 날짜의 점선·추정값 없는 날짜의 빈 원을 구분합니다. 인라인 SVG 탐색 아이콘은 20px와 stroke 1.6, 선택창 꺾쇠는 18px와 stroke 1.8입니다. 장식 SVG에는 `aria-hidden`을 둡니다. 앱과 독립 보고서의 favicon은 잉크색 바탕의 금색 번개 기하를 사용합니다.

## Components

### Buttons

기본은 잉크 바탕·흰 글자, secondary와 링크형 조작부는 흰 바탕·잉크 글자·조작부 경계입니다. 패딩과 모서리는 frontmatter가 기준입니다. hover는 배경·경계만 150ms 동안 전환하고 비활성은 불투명도 0.45와 기본 커서입니다. 밝은 면의 포커스는 파랑, 어두운 면은 금색입니다.

차트 이전·다음 버튼은 어두운 영역의 별도 색을 사용하며 날짜 경계에서 비활성화합니다. 검토 필터는 투명 바탕에서 선택 시 옅은 파랑·진한 파랑 문자·경계로 바뀌고 `aria-pressed`를 사용합니다. 작은 화면에서는 필터를 2×2로 배치합니다. `prefers-reduced-motion: reduce`에서는 버튼 전환과 1초 선형 로딩 회전을 멈춥니다. 탐색·모달·차트에 장식적인 등장 모션은 없습니다.

### Chips

상태 배지는 짧은 상태명과 옅은 배경의 비조작 요소입니다. 완료는 녹색, 검증 완료는 황토색, 실패는 적색, 실행 중은 중립색입니다. 보고서 기간 태그는 어두운 합계 면에서 `nav-active` 배경과 흰 글자를 사용합니다. 색만으로 품질이나 서비스 상태를 판단하게 하지 않습니다.

### Cards / Containers

품질 패널은 큰 비율, 3분류 트랙과 수치 행, 슬롯 완전성 설명, 원본 보간의 별도 설명으로 구성합니다. 흰 패널 기본 여백은 28px, 어두운 분석 면은 28px 32px입니다. 출처 띠는 푸른 회색 면에 자료 범위·추정 해석·공개 자료의 저자와 라이선스를 함께 표시합니다. 합성·공개·혼합·없음 상태의 문구는 구분합니다.

### Inputs / Fields

검색 입력은 흰 면·조작부 경계와 보이는 레이블을 사용합니다. placeholder는 레이블을 대체하지 않습니다. 목록 선택은 원래 select의 값과 change 이벤트를 보존하면서 보이는 combobox trigger와 listbox popover로 확장합니다. trigger에 레이블·`aria-expanded`·`aria-controls`를 연결하고 항목에 `aria-selected`·`aria-disabled`를 둡니다.

목록은 방향키·Home/End·Enter/Space·문자 검색을 지원합니다. Escape·Tab과 바깥 클릭은 닫고, 선택 후 trigger로 포커스를 돌립니다. 문서 스크롤·창 크기/visual viewport 변경에도 열린 상태를 유지하며 animation frame마다 trigger 좌표에 다시 붙입니다. trigger가 완전히 화면 밖으로 나가면 닫습니다. 목록 내부 스크롤과 키보드 탐색은 목록만 움직입니다. 팝업은 화면 가장자리 12px을 확보하고 위/아래 가용 공간에 맞춰 최대 320px로 제한합니다. 숨긴 원래 select를 별도의 두 번째 탭 정지점으로 만들지 않습니다. [현재 동작 검증](docs/benchmarks/select-anchor-20261023.md).

월 trigger는 이름 있는 dialog를 엽니다. 최대 너비는 `min(440px, calc(100vw - 32px))`입니다. 연도 입력과 이전·다음 연도, 3열×4행 월 버튼, 취소로 구성하며 연도 범위는 1900–2199입니다. 현재 월은 잉크 바탕·금색 문자와 `aria-pressed`, 방향키는 좌우 1칸·상하 3칸 이동입니다. 열 때 현재 월에 포커스를 두고, 모달 닫힘은 브라우저의 dialog 포커스 복귀를 사용합니다. 월 입력의 값과 change 이벤트는 기존 데이터 계약입니다.

### Navigation

분석(전체 현황·발전소·데이터 품질), 감사 자료(월간 보고서·실행 이력·데이터 출처), 관리(시스템 관리)의 세 그룹입니다. 비활성 항목은 탐색 회청색, hover는 탐색 잉크, 현재 항목은 선택 잉크·흰 글자·금색 아이콘과 `aria-current="page"`입니다. 이전 수평 메뉴의 금색 밑줄은 현재 사이드바 규칙이 아닙니다.

900px 이하에서는 메뉴 버튼이 `aria-expanded`로 공개 여부를 알리고 문서 흐름에서 탐색을 펼칩니다. Escape는 닫고 버튼으로 포커스를 돌립니다. 오버레이나 포커스 가두기를 추가하지 않습니다. 본문 바로가기는 포커스 때 표시합니다. 분석 URL은 화면·월·자료 구분과 해당 화면의 필터를 반영하며 관리 화면으로 이동할 때도 월·자료 구분을 전달합니다.

### Run History

사용자 요청에 따라 작업형 제목은 “처리 과정을 확인하기”처럼 `~하기`로 씁니다. 이미 명사형인 화면 제목은 유지합니다. 상세의 진단 조회는 명시적으로 눌렀을 때만 실행하며 실패 근거·현재 게시 결과·같은 날짜의 다른 활성 실행 링크를 함께 제공합니다. 경과 시간만으로 실패를 확정하지 않습니다.

실행 이력은 전체 처리 기간의 공개·합성 기록을 조회합니다. 보고 월·자료 구분은 이 화면의 필터가 아니며 범위를 본문에 설명합니다. 실행 단위·상태 선택창과 정확히 일치하는 발전소 ID 입력, 조회·새로고침·필터 초기화를 사용합니다. 요약 건수는 실행 단위·발전소 기준이며 상태 필터 적용 전입니다.

`level/status/run_plant/offset/run`을 URL에 보존하고 새로고침·뒤로/앞으로 가기로 복원합니다. 기본값·잘못된 값은 정규화하고 범위를 벗어난 페이지는 마지막 유효 페이지로 이동합니다. 상세·하위 파티션·상위 작업은 실제 href를 갖습니다. 하위/상위 이동은 단위를 바꾸고 상태·페이지를 초기화합니다. [실제 검사·화면](docs/worklog/2026-10-23-run-navigation.md).

### Energy Chart and Quality Ledger

월 합계는 MWh, 일별 수치표와 보고서는 kWh입니다. 날짜별 막대는 선으로 연결하지 않으며 해당 날짜의 포함 발전소 수를 보여 줍니다. 미등록 날짜·등록됐지만 추정값 없음·실제 0을 구별합니다. 차트는 pointer·키보드·상세 날짜 선택창·이전/다음 버튼과 펼치는 수치표를 제공합니다. 원본 보간은 유효·무효와 중첩할 수 있으므로 3분류 품질 트랙에 합산하지 않습니다.

15분 관측 차트는 전력 실선·POA 점선과 좌우 단위를 사용합니다. 유효값 없음은 선을 끊고 별도 띠·개수·펼치는 UTC 범위로 설명합니다. 0은 유효한 값이며 단일 관측은 점, 15분 초과 간격은 끊김으로 표시합니다. SVG의 좌표 폭을 실제 CSS 폭에 맞춰 14px 글씨를 유지합니다. 관측값 표는 이름 있는 포커스 가능 영역으로 키보드 가로 탐색을 지원합니다. [후속 상호작용 검증](docs/benchmarks/interactions-20261023.md).

### Integrated Report

빈 월에서는 실제 발행 월 목록을 안내합니다. 전체 현황·발전소·품질·출처의 빈 월은 게시된 일별 자료의 월 목록을 사용하며, 자료 등록과 보고서 발행을 구분합니다. 월 목록을 바꾸는 것만으로 화면을 전환하지 않고 이동 링크로 선택을 실행합니다.

보고서 합계 다음에 생성 기준 시각(자료 조회 시작)·입력 버전·계산 버전을 표시합니다. 이후 적재·재처리·버전 변경 결과는 재발행해야 반영됨을 설명합니다. 기존 UUID의 출력물을 수정하거나 실시간 동기화 상태를 추측하지 않습니다.

보고서 선택과 CSV·출처 JSON·독립 인쇄 링크 아래에 합계 띠 → 자료 출처 → 품질 정의 목록 → 펼치는 일별 내역 → 품질 메모·검토 후보 → 계산과 원본 계보를 배치합니다. 현재 선택의 manifest를 읽어 article로 구성하며 iframe나 내부 세로 스크롤을 만들지 않습니다. 품질 이슈와 검토 후보는 각각 첫 12건과 전체 JSON 경로를 표시합니다.

독립 HTML은 같은 report.css와 용어를 사용하며 일별 표를 바로 표시합니다. 인쇄 버튼은 출력 때 숨깁니다. 화면 스타일을 갱신한 새 보고서를 발행해도 원래 UUID의 산출물은 보존합니다. 구체적인 발행·비교 근거는 검증 문서에 둡니다.

### Independent Administration

사이드바의 시스템 관리는 중간 페이지 없이 독립 관리 화면으로 이동합니다. 예전 `?view=system` 주소도 이동합니다. 127.0.0.1:8504의 호스트 관리 프로세스는 같은 탐색·글꼴·조작부를 사용합니다. 엔진 연결·마지막 확인 시각·최근 작업은 공통 영역이고, 서비스 제어 / 컨테이너 상태 / 운영 안내는 하나씩 표시하는 탭입니다. tablist/tab/tabpanel, 방향키·Home/End, `#services/#containers/#guide` 직접 주소를 지원하며 월·출처를 보존합니다.

서비스 행은 대상·설명·실행 개수와 시작/중지 버튼입니다. 확인 dialog는 영향을 받는 서비스와 데이터·볼륨 보존을 설명하고 취소에 초기 포커스를 둡니다. 조작 중·상태 조회 중·엔진 연결 불가 때는 제어를 비활성화합니다. 5초 조회는 조작 노드를 교체하지 않아 포커스와 열린 dialog를 유지합니다. 실패는 문자와 적색으로 표시하며 결과를 확인하지 못한 요청은 자동 재시도하지 않습니다. 실행·건강·준비를 서로 다른 열로 표시합니다.

## Do's and Don'ts

### Do:

- **Do** 추정 에너지와 단위, UTC 날짜, 현재 자료 출처를 함께 표시합니다.
- **Do** 데이터 품질의 문자·수치·도형과 별도의 원본 보간 설명을 유지합니다.
- **Do** 본문 16px와 화면 보조 글씨 최소 14px, 명시적 레이블과 키보드 포커스를 유지합니다.
- **Do** 사이드바의 세 그룹과 현재 위치, 작은 화면의 메뉴 열기·닫기를 유지합니다.
- **Do** 보고서를 메인 문서에 이어 붙이고 일별 내역과 원본 계보를 펼쳐 읽게 합니다.
- **Do** 관리 조작 전에 대상·의존 서비스·영향을 설명하고 실행·건강·준비 상태를 구분합니다.
- **Do** 검증 보고서의 실제 실행 결과와 검증하지 않은 환경을 구분합니다.

### Don't:

- **Don't** 자료 없음이나 추정값 없음을 0 발전량으로 표시하지 않습니다.
- **Don't** 원본 보간을 유효·무효·누락과 상호 배타적인 네 번째 품질 분류로 합산하지 않습니다.
- **Don't** 검토 후보를 확정 고장·금전 손실·실시간 운영 성과로 표현하지 않습니다.
- **Don't** 보고서에 iframe나 별도의 세로 스크롤 영역을 다시 넣지 않습니다.
- **Don't** 시스템 조작을 읽기 전용 분석 화면에 섞거나 실제 컨테이너 실행을 모든 서비스의 준비 완료로 표현하지 않습니다.
- **Don't** 원래 UUID의 보고서와 원본 데이터를 새 화면 양식으로 덮어쓰지 않습니다.
- **Don't** 장식용 데이터·보간선·외부 글꼴 의존성을 추가하지 않습니다.
