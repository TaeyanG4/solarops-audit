# 워크스페이스·보고서·로컬 관리 검증

2026-10-23 Asia/Seoul. [현재 디자인](../../DESIGN.md) · [방향과 추가 요건](../design/workspace-navigation.md) · [작업 기록](../worklog/2026-10-23-workspace.md).

## 사용자 지시와 최종 범위

수평 탐색 중간안 이후 사용자가 사이드바·기능 그룹·관리 탭을 지정했습니다. 이후 favicon·선택창·작은 글씨·옛 보고서 양식·페이지 안의 페이지 구조를 지적했습니다. 최종 화면은 분석 3개, 감사 자료 3개, 관리 1개의 목적지와 16px 본문/최소14px 보조 글씨, 키보드 가능한 공통 선택창을 사용합니다.

월간 보고서는 manifest JSON에서 메인 DOM으로 직접 그립니다. iframe와 내부 세로 스크롤을 없애고 요약, 품질 정의 목록, 펼치는 일별 내역, 검토 후보, 계산/원본 계보로 구성했습니다. 독립 인쇄용 HTML도 같은 CSS·자체 포함 Pretendard/OFL을 사용합니다. 데이터 처리·기존 API 계약은 유지합니다.

## 실제 화면

| CSS 너비 | 중간안 전체 현황 | 최종 전체 현황 | 최종 월간 보고서 | 최종 시스템 관리 |
|---|---|---|---|---|
| 1440px | [이전](../portfolio/images/workspace-20261023/before-1440.png) | [현재](../portfolio/images/workspace-20261023/overview-1440.png) | [보고서](../portfolio/images/workspace-20261023/reports-1440.png) | [관리](../portfolio/images/workspace-20261023/admin-1440.png) |
| 768px | [이전](../portfolio/images/workspace-20261023/before-768.png) | [현재](../portfolio/images/workspace-20261023/overview-768.png) | [보고서](../portfolio/images/workspace-20261023/reports-768.png) | [관리](../portfolio/images/workspace-20261023/admin-768.png) |
| 390px | [이전](../portfolio/images/workspace-20261023/before-390.png) | [현재](../portfolio/images/workspace-20261023/overview-390.png) | [보고서](../portfolio/images/workspace-20261023/reports-390.png) | [관리](../portfolio/images/workspace-20261023/admin-390.png) |

같은 공개2024-04 자료, DPR2, viewport 높이1000px. 이전은 전체 페이지, 현재는 첫 viewport로 캡처 범위가 다릅니다. [월 선택](../portfolio/images/workspace-20261023/month-picker-mobile.png) · [목록 선택](../portfolio/images/workspace-20261023/source-options-mobile.png) · [펼친 일별 내역](../portfolio/images/workspace-20261023/report-daily-mobile.png) · [독립 인쇄 HTML](../portfolio/images/workspace-20261023/print-report-1440.png). 이미지 원본·크롭·픽셀 크기는 [이미지 정보](../portfolio/images/workspace-20261023/README.md)에 있습니다.

## 실행한 검사

| 검사 | 결과 | 로컬 원본 증거 (`artifacts/ui-workspace-20261023/`) |
|---|---|---|
| Python 오프라인 회귀 | **126 passed, 6 skipped** | `pytest.xml` |
| Ruff check/format | 통과,69개 파일 형식 확인 | 명령 실행 결과 |
| JS 문법 | dashboard/controls/navigation/admin 네 파일 통과 | `node --check` |
| wheel | 빌드 성공, admin HTML/Python·선택창·보고서 CSS·폰트/OFL·템플릿 포함 확인 | `dist/solarops_audit-0.4.1-py3-none-any.whl` |
| GitHub CI (`0618ce1`) | Windows/Ubuntu 각각 **127 passed,5 skipped**, 합성 데모·복원·wheel·소스 ZIP 성공 | [run39841897047](https://github.com/TaeyanG4/solarops-audit/actions/runs/39841897047), `github-ci.json` |
| 전체 현황 브라우저 회귀 | **107명령**,3너비 axe 위반0 | `overview-final/` |
| 워크스페이스 브라우저 | **195명령**,23회 axe 위반0, API 응답 동일 | `workspace-reviewed/` |
| 실제 서비스 수명주기 | **132명령**,15회 axe 위반0, 전체 중지→기본 시작→kind 시작 | `workspace-check/lifecycle.json` |
| 선택창 추가 확인 | 보고서 선택 Home/End/Enter, 연결된 aria-controls·선택 항목·활성 후손 확인 | `final-capture-checks.json` |

Agent Browser0.39.1 / Chrome156 / axe-core4.12.1. overview 검사는 필터·깊은 링크·뒤로 가기·null과0·부분 기간·합성/혼합·빈값/오류 복구·reduced-motion·320px 넘침을 포함합니다. workspace 검사는 새 화면5개와 관리, 월 선택/취소/없는 기간, 소스 선택 키보드, 모바일 메뉴/Escape, iframe 없음·일별30행·출처 펼침, 독립 HTML3너비, 조작 취소를 포함합니다. 가시적인 p/td/th/label/button/nav a가14px 이상인지 확인했습니다.

axe가 popover combobox의 `aria-controls`를 수동 확인 대상으로 남겨 실제 연결된 ID·aria-selected·aria-activedescendant를 추가 검사했습니다. 위반0은 접근성 인증이 아닙니다. 실제 휴대폰·Firefox/Safari·스크린리더·인쇄된 PDF 페이지 나눔은 검증하지 않았습니다.

## 관리 서버 확인 범위

14개 관리 테스트는 소속/로컬 context 검사, Host/Origin/CSRF 거부, 허용 목록, 의존성 순서, 동시 조작, 실패·감사 기록을 확인합니다. 실제 브라우저로 프로젝트 전체를 멈추고 기본3개와 kind를 복구했습니다. 독립8504는 계속 응답했고 다른 프로젝트 `codex-lb`는 실행 상태를 유지했습니다. 조회 API 내용도 전후 동일했습니다.

Compose Airflow는 이 검사 전후 중지 상태입니다. kind 노드의 시작은 확인했지만 이번 수명주기 검사로 내부 모든 Pod의 준비 상태나 새 KPO 처리를 재인증하지 않습니다. 기존 컨테이너가 있어야 하며 삭제·생성·원격 Docker·엔진 제어는 범위 밖입니다. [운영 안내](../runbooks/operator.md#시스템-관리-8504).

## 보고서 보존과 새 발행

- 기존UUID의 HTML/CSV/manifest는 덮어쓰지 않았고 HTTP200으로 계속 조회됩니다. 새 PS_001 보고서 `d9a964f0-8846-4785-8989-9d392c7927a3`는585,980.279kWh, 유효74.9%, 보간17.01%로 기존 지표·원본 계보 hash와 같습니다.
- 기존 `all` 보고서는 합성7파티션만 담은 과거 스냅샷이었습니다. 새 발행은 현재 카탈로그의 공개+합성147파티션,1,478,661.270kWh를 포함하므로 기존 값과 같다고 주장하지 않습니다. 계산 변경이 아니라 스냅샷 시점 차이입니다.
- `all-public` 지표는 동일하나 이전 발행 뒤 PS_0014월3일 파티션이 새 버전으로 게시되어 원본 계보 hash가 달라졌습니다. 과거 snapshot도 보존합니다.
- 마지막 폰트 라이선스 포함 발행은 직전 신규 보고서4개와 지표/계보 hash가 모두 같습니다. `report-regeneration.json`과 `report-final-regeneration.json`에 ID·비교 결과를 남겼습니다. 새 all/public/DEMO 보고서도 임의 raw 재처리 없이 현재 게시된 snapshot을 사용합니다.

## 디자인 검수

UI UX Pro Max는 운영 탐색 위계를 참고했고 부적합한 landing/CTA·Fira 제안은 적용하지 않았습니다. Impeccable detector는 변경 대상에 한 번 실행했습니다.64항목 중63개는 이전 DESIGN.md와 현재 추가 토큰 간의 advisory,1개는 `/static/dashboard.css` 경로를 admin 폴더에서 해석하지 못한 정적 글자 위계 경고입니다. 실제 화면과 코드의 제목/본문 위계를 함께 검수합니다. detector0건으로 기록하지 않습니다.

최신 사용자 지시·첨부 이미지·방향 계약·실제 캡처·코드를 전달한 **별도 fresh finish reviewer의 판정은 `ship`**입니다. persistence/fidelity/ceiling/material_fixes/keep 다섯 항목을 확인했고 해당 UI범위의 material fix는 없었습니다. 제공한 캡처/코드에 대한 검수이며 독립 브라우저 실행·고객 평가·백엔드 보안 인증을 주장하지 않습니다. 로컬 `finish-review.md`에 원문을 보존합니다.

검수 중 fixed sidebar가 어긋난 보조 admin full-page 캡처를 발견해 증거에서 제외했습니다. 문서에는 정상적으로 다시 찍은 시작 viewport와 유효한 상세 viewport만 사용합니다. 이전 수평 탐색안의 ship 결론을 재사용하지 않았습니다. 별도 documenter가 실제 소스에서 최종 [DESIGN.md](../../DESIGN.md)와 [.impeccable/design.json](../../.impeccable/design.json)을 갱신했습니다. 사이드바·16/14px·popover·통합/독립 보고서·관리 컴포넌트와 실제 CSS 우선순위를 기록했습니다.

## 재현

준비된8502공개·합성 자료와8504관리 서버, Agent Browser가 필요합니다. 오프라인 CI에서 원본 전체 자료를 다운로드하지 않습니다.

```text
uv run python scripts/validation/overview_browser.py --output artifacts/overview-new-check
uv run python scripts/validation/workspace_browser.py --output artifacts/workspace-new-check
```

실제 가용성까지 변경하는 검사는 마지막 명령에 `--lifecycle`을 명시합니다. 처리 중인 Airflow/worker가 없는 상태에서 실행하며 기본 모드는 조회와 취소만 검사합니다.
