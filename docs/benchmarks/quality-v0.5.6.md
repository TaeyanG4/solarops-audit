# v0.5.6 보고서 선택·품질 집계·재현 근거

2026-10-23 Asia/Seoul. 계산energy-interval-v2 유지. [기계 판독 요약](quality-v0.5.6.json) · [수행 기록](../worklog/2026-10-23-quality-r5.md).

- 보고서의 표시scope와 선택키를 분리. `all`/`all-public`/`all-synthetic` 발전소 각2선택+전체2선택의 8개 최신 보고서 공존, 기존 display키 행 보존·읽기 중복해소·기존manifest 바이트와 freshness 유지 확인. SQLite·PostgreSQL의 기존 역순게시 검사에 같은 경계를 확장했습니다.
- v2 `warning_count`는 분석규칙 부분집합임을 명시하고 새 API/보고서CSV의 `quality_issue_count`로 입력 중복 포함 전체이슈를 제공합니다. 합성4월1일 경고0·총이슈1, 정상합성7일1,342행의 이전논리hash 동일. source_version 라벨 포함과 보고서freshness의 발행계보 기준을 구분합니다.
- `analyze`는 읽기 전용 Catalog와 dispose를 사용. 없는 SQLite DB가 생기지 않는 경계를 기존 CLI검사에 추가했습니다.
- 오프라인140통과·14제외35.03초, 실제격리 PostgreSQL/MinIO13통과25.46초, Ruff77파일/JS문법 통과. 인쇄템플릿 최종변경 후 해당 보고서 검사1통과2.50초. 전체ruff 최초범위(.)에는 보존대상docs/plan 원본의 import순서 지적1건이 있었으며 원본은 수정하지 않고 CI와같은 src/tests/scripts/dags범위로 통과했습니다.
- Agent Browser의 독립 합성preview에서 1440/768/390px 선택라벨·8개목록·정확한발행UUID전환·뒤로가기·가로넘침없음을 확인. 390px axe36pass/0violation/1incomplete(숨긴popover aria-controls참조 대상이 DOM에 있음을 직접확인). 열린popover색대비는 자동판단불가2노드이며 새색상변경없음. 해당preview8505/브라우저종료·자료보존. 모바일제목의 한국어단어줄바꿈을 보완했습니다.
- 과거 합성조회1,080개 [지연표본·산식](evidence/technical-20261023/README.md)을 추가. 전27조건 p50/p95·오류수를 재계산해 원요약과 일치. 새성능실측이 아니며 영구부하suite를 추가하지 않았습니다.

새 active키는 기존행을 삭제하지 않습니다. 선택미기록/파일조회불가인 과거 보고서는 추측해 합치지 않으며 과거충돌로 가려진 보고서를 자동복원하지 않습니다. [호환/집계 계약](../data-contract.md#보고서-선택과-품질-건수-v056). 인버터 관측분모/장기조회물질화 한계는 유지합니다. 배포·CI도 완료했습니다.

[구현4b9959e/이미지](../releases/0.5.6.json)의0.5.6을 Compose대시보드·kindAirflow/KPO에 반영했습니다. health0.5.6/ready·kind6서비스PodReady·3rollout성공·양모드7DAG정상. ComposeAirflow3개는생성후중지. [CI39936889247](https://github.com/TaeyanG4/solarops-audit/actions/runs/39936889247) Windows/Ubuntu성공. 공개overview·ONS응답동일, 기존보고서3ID와 기존필드응답동일(selection추가필드는비교제외). 원본·과거보고서재발행/삭제없음. 새정기KPO나공개전체재처리를이번버전에서실행했다고주장하지않습니다.
