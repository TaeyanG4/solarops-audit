# v0.5.5 원본 진단·인버터 계보 검증

2026-10-23 Asia/Seoul. 계산energy-interval-v2 유지. [기계 판독 요약](quality-v0.5.5.json), [작업·한계](../worklog/2026-10-23-quality-r4.md).

- 원본 캡처/로컬raw/S3메타데이터의 SHA불일치를 BR/ONS공통 `RAW_OBJECT_CHECKSUM_MISMATCH`로 구별합니다. 원문 값·경로·접속 정보를 출력하지 않습니다. 기존 캡처손상·ONS실패코드 검사로 확인했습니다.
- 새 일별 manifest의 `source_inverter_bounds`는 해당 날짜와 겹치는 원본 인버터 ID/전체관측범위를 보존합니다. 새 보고서HTML·대시보드·CSV·계보JSON의 `source_inverter_count`는 그 개수이며 설치된 설비대수가 아닙니다. 과거manifest 미기록은null/기록없음, 기존보고서 불변을 기존검사에서 확인했습니다.
- 오프라인140통과·14제외33.72초, 실제격리 PostgreSQL/pinnedMinIO13통과23.24초. Ruff76파일·JS문법 통과. 새 영구검사함수/전용검증스크립트 없음.
- 정상합성7일1,342행 논리hash가 이전기준과동일합니다. source-bound인버터 제거시 기대슬롯1,344→672라는 기존제한은 변하지 않으며 이제 새manifest/보고서에서 ID/범위/개수를조회할수있습니다. 공개전체재처리/원본수정/과거보고서재발행은하지않았습니다.
- Agent Browser의 별도합성preview에서 1440/390px 새 인버터2개표시·가로넘침없음을 확인했습니다. 이미지 `artifacts/portfolio-quality-r4-20261023/inverters-1440.png`, `inverters-390-detail.png`; preview8505와 해당브라우저는종료하고 자료는보존했습니다.

이번 변경은 계산/다운로드/스케줄을 바꾸지 않습니다. [v0.5.4의 저장소 배포](quality-v0.5.4.md), [v0.5.3의 범위 계산 비용](quality-v0.5.3.md)은 과거근거로 보존합니다. 앱0.5.5배포·CI는 진행중이며 아래에 실제결과를추가합니다.
