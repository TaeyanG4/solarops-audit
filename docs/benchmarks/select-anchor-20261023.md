# 목록 선택창을 연 채 스크롤

2026-10-23 (Asia/Seoul). 사용자는 UI-04의 ‘스크롤 시 닫힘’도 원하는 동작이 아니라고 지적했습니다. 기존 검사는 구현한 닫힘을 확인했을 뿐, 목록을 계속 사용하는 요구를 검증하지 못했습니다. 이번 수정은 열린 상태를 유지하고 선택 버튼의 위치를 따라가도록 바꿉니다.

## 현재 동작

- 페이지 스크롤·화면 크기 변경 때 선택 버튼의 좌표를 다시 읽고 열린 목록을 붙입니다. 위치 갱신은 animation frame마다 한 번으로 묶습니다.
- 가용 공간에 맞춰 버튼 아래/위로 배치하고 화면 가장자리 여백을 확보합니다. 목록 내부 스크롤·현재 강조 항목은 유지합니다.
- 항목 선택, Escape, Tab, 바깥 클릭으로 닫습니다. 버튼이 화면 밖으로 완전히 벗어나면 홀로 뜬 목록을 남기지 않도록 닫습니다.
- native select의 값/change 계약과 키보드 탐색은 유지합니다. API·계산·자료와 관리 기능은 변경하지 않았습니다.

## 재현과 검증

기준 `21bf2ff`에서 새 검사를 실행하자 페이지180px 스크롤 뒤 ‘목록이 열려 있고 버튼과 붙어 있음’ 검사가 실패했습니다. 수정한 이미지로 같은 검사를 실행해 통과했습니다. 실패 로그와 스크린샷도 보존했습니다.

| 확인 항목 | 실제 결과 |
|---|---|
| Agent Browser | **269명령**, 1440/768/390px, 실제 Chromium |
| 보고서·실행 이력 목록 | wheel180px 내려가기·90px 올라가기, 목록 열림 유지와 버튼 간격6px(허용오차1px 미만) |
| 창 크기·경계 | 높이1000→800→1000에도 열림·배치 유지. 목록은 화면 경계 안에 위치 |
| 긴 날짜 목록 | 내부 스크롤, Home/End/Enter로 첫날·마지막 날 선택, 배경 페이지 위치 유지 |
| 닫힘·포커스 | Escape·Tab·바깥 클릭, 버튼이 화면에서 완전히 나간 경우 닫힘, Escape 포커스 유지 |
| 접근성·계약 | 열린 목록 axe6회 위반0, JS 오류0, overview/시계열 API와 관리operation 전후 동일 |
| 정적·배포 | JS 문법·Ruff·70파일 형식 통과. HTTP controls.js SHA-256이 로컬 소스와 일치 |

```text
uv run python -u scripts/validation/interaction_browser.py --selectors-only --output artifacts/select-anchor-new
```

`--selectors-only` 없이 실행하면 관리 탭·시계열도 검사합니다. 이번에는 변경된 목록 동작 범위만 실행했습니다. 전용 브라우저는 검사 종료 시 닫았으며, DB 쓰기·관리 시작/중지·원본 다운로드는 하지 않았습니다.

## 화면과 전달

| 대상 | 캡처 |
|---|---|
| 이전 닫힘 처리 | [UI-04 스크롤 후 닫힌 보고서](../portfolio/images/interactions-20261023/reports-scrolled-390.png) |
| 수정한 보고서 | [1440px](../portfolio/images/select-anchor-20261023/reports-scrolled-1440.png), [768px](../portfolio/images/select-anchor-20261023/reports-scrolled-768.png), [390px](../portfolio/images/select-anchor-20261023/reports-scrolled-390.png) |
| 수정한 실행 이력 | [1440px](../portfolio/images/select-anchor-20261023/runs-scrolled-1440.png) |

[촬영 조건·출처](../portfolio/images/select-anchor-20261023/README.md). 새 dashboard 이미지 `solarops-worker:0.4.1-select-anchor-20261023`을 배포하고 controls.js 캐시 식별자를 변경했습니다. DB·MinIO·kind는 재생성하지 않았습니다. [이미지 SHA](../image-versions.json).

로컬 상세 증거는 Git 제외 `artifacts/select-anchor-20261023/`의 `before/checks.json`, `verified/{checks,summary}.json`, `deployment.json`, `impeccable.json`에 있습니다. 실제 기기·핀치 확대·모바일 가상 키보드·Safari/Firefox·스크린리더는 이번 검증 범위 밖입니다.

UI UX Pro Max의 키보드/포커스 가이드, Impeccable harden·craft-floor의 상태/경계 검수, Agent Browser의 실제 스크롤·화면·axe 검사를 사용했습니다. controls.js에 한정한 Impeccable detector 결과는 `[]`이며 전체 앱 품질 인증을 뜻하지 않습니다.
