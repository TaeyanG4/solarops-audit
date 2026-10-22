# 작은 글자 가독성을 보완한 캡처

2026-10-23, SolarOps v0.4.1. 이전 1440px 전체 화면을 README 본문으로 축소하면 14px 글자가 약 8px 크기가 됩니다. 이번에는 **820 CSS px 반응형 화면을 deviceScaleFactor=2로 새로 렌더링**했습니다. 실제 픽셀 수와 문서 표시 크기를 분리해 글자 크기와 선명도를 함께 확보합니다.

Agent Browser CLI 0.39.1 / Chrome 155의 실제 로컬 화면입니다. 기존 PNG를 늘리거나 글자를 다시 그리지 않았습니다. 아래 영역은 원본 전체 캡처에서 픽셀 크롭만 했으며, 데이터·스타일·문구를 조작하지 않았습니다. 캡처 환경은 앱 실행 의존성이 아닙니다.

| 원본 이미지 | 실제 PNG 픽셀 | 자연스러운 표시 폭 | 내용 |
|---|---:|---:|---|
| [전체 현황](overview.png?raw=1) | 1640×2548 | 820 CSS px | 공개 2024년 4월, 필터·KPI·일별 차트 |
| [발전소 비교](plants.png?raw=1) | 1592×1020 | 796 CSS px | 5개 중 첫 두 항목 PS_001·PS_005 발췌 |
| [일별 차트](daily-chart.png?raw=1) | 1592×1264 | 796 CSS px | 날짜 탐색·추정 MWh |
| [품질 분류](quality.png?raw=1) | 1592×726 | 796 CSS px | 유효·무효·누락과 별도 원본 보간 설명 |
| [모바일 차트](mobile-chart.png?raw=1) | 780×1316 | 390 CSS px | 390px 실제 반응형 화면 |
| [합성 실패 근거](run-evidence.png?raw=1) | 1592×1002 | 796 CSS px | DEMO_01 / synthetic-v1 커밋 실패 주입 |

공개 현황은 `view=overview&period=2024-04&source=public`, 합성 실패는 `view=runs`에서 조회했습니다. 실행 이력의 `INJECTED_DURING_COMMIT`는 복구 검증을 위한 합성 실패이며 현장 장애가 아닙니다.

README에는 두 이미지를 배치하고 세부 영역과 원본 확대 링크를 제공합니다. GitHub의 실제 본문 폭은 창·사이드바에 따라 다릅니다. 특히 휴대폰에서는 원본 링크를 열어 확대하세요. 본문 폭 820px 및 390px의 로컬 문서 미리보기에서 이미지 로딩·비율·넘침을 확인하며, 이것을 GitHub 전체 UI의 픽셀 동일성 검증으로 표현하지 않습니다.

원본 전체 캡처·복구 응답·표시 크기 검사는 Git 제외 `artifacts/recovery-images-20261023/`에 보존합니다. [이전 이미지](../readme-20261023/README.md)와 [리디자인 전후 증거](../../../benchmarks/overview-redesign-20261023.md)는 당시 기록으로 유지합니다.
