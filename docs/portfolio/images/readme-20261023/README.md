# README와 사례 문서의 최신 이미지

2026-10-23, 앱 v0.4.1 전체 현황 리디자인 이후의 **실제 로컬 화면**입니다. Agent Browser CLI 0.39.1 / Headless Chrome 155로 캡처했습니다. 생성 이미지나 임의의 수치 목업이 아닙니다.

| 파일 | 자료와 화면 | 캡처 범위 |
|---|---|---|
| [overview.png](overview.png) | 공개 BR-PVGen, 2024년 4월 전체 현황 | 1440×1080 뷰포트 |
| [plants.png](plants.png) | 같은 공개 월의 5개 발전소 품질 표 | 1440px 전체 페이지에서 표 영역 크롭, 1200×623 |
| [mobile-chart.png](mobile-chart.png) | 같은 공개 월의 일별 추정 에너지·날짜 탐색 | 390px 전체 페이지에서 차트 영역 크롭, 390×658 |
| [run-evidence.png](run-evidence.png) | DEMO_01 / synthetic-v1의 의도적 커밋 실패 | 1440px 실행 이력 페이지에서 선택 상세 크롭, 1200×509 |

크롭은 원래 픽셀에서 영역만 잘랐으며 수치·문구·화면 구성은 수정하지 않았습니다. 실행 이력은 자료 필터와 별개로 모든 작업 종류를 보여주므로 마지막 이미지는 **공개 발전소 장애가 아닌 합성 복구 검사**입니다. 오류 코드는 `INJECTED_DURING_COMMIT`입니다.

화면 URL은 로컬 서버 `http://127.0.0.1:8502/`의 `view=overview&period=2024-04&source=public` 및 `view=runs`입니다. 원본 전체 캡처와 출처 메타데이터는 Git 제외 `artifacts/docs-refresh-20261023/`에 보존합니다.

이번 작업은 문서 이미지 갱신입니다. 세 너비의 기능·접근성 검사와 리디자인 전후 이미지는 기존 [UI 검증 보고서](../../../benchmarks/overview-redesign-20261023.md)에 있습니다. 과거 화면은 당시 증거로 남겨 두고 현재 README와 [사례 문서](../../CASE_STUDY.md)만 새 이미지로 연결했습니다.
