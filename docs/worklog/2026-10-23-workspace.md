# 2026-10-23 사이드바·시스템 관리·보고서 작업

최종 구현·로컬 검증 기록. [상세 검사와 증거](../benchmarks/workspace-20261023.md), [최신 이미지](../portfolio/images/workspace-20261023/README.md), [운영 순서](../runbooks/operator.md#시스템-관리-8504).

## 기능 그룹과 사이드바

- 사용자 요청으로 수평 탐색을 분석(전체 현황·발전소·품질), 감사 자료(보고서·실행·출처), 관리(시스템)의 7개 목적지로 교체했습니다.
- 새 발전소·품질·출처 화면은 기존 읽기 API를 재사용합니다. [방향 계약](../design/workspace-navigation.md), Energy Desk 색·폰트는 유지합니다.
- 최종 검사: overview107명령·axe3회 위반0, workspace195명령·axe23회 위반0,1440/768/390px·320px넘침·메뉴/Escape·깊은 링크·선택값 확인. 증거 `artifacts/ui-workspace-20261023/`.
- 현재 기준은 사이드바이며 이전 수평 Energy Desk 이미지와 검수는 중간 이력으로 보존합니다. API 응답은 변경 전후 동일합니다.

## 독립 로컬 관리 서버

- `solarops admin`을 호스트 loopback 8504에서 실행합니다. Docker 안의 읽기 API(8502)와 분리하며, Host·Origin·CSRF token·동시 작업 lock·고정 허용 목록·소속 라벨/체크아웃 검사를 적용했습니다.
- 기존 컨테이너만 시작/중지합니다. 삭제·SQL·임의 shell·Docker 엔진 중지는 없으며, 조작 기록은 제외 경로 `artifacts/ops/admin-actions.jsonl`에 보존합니다.
- Compose DB/MinIO/Airflow와 Kubernetes 안의 별도 DB/MinIO/Airflow를 구분했습니다. DB/저장소 중지는 Compose 소비자를 먼저 멈추고, 전체 중지는 kind도 포함합니다.
- 실제 UI로 전체 중지→기본 3서비스 재시작→kind 재시작 통과. API 응답 동일, 다른 `codex-lb` 유지. `workspace-check/lifecycle.json`에 상태를 보존했습니다.
- 14개 오프라인 관리 테스트, 최종 전체 Python126통과·6제외. Windows 실행기 자식 프로세스와 건강 검사 없는 Docker 객체 처리를 수정했습니다.

## 사용자 추가 요청 — favicon·선택창·가독성·보고서

- 첨부 이미지에서 기본 월 선택창, 일부 기본 목록, 작은 글씨와 보고서 iframe/옛 양식을 지적했습니다. 고정된 새 요건으로 반영합니다.
- SVG favicon, ARIA combobox/listbox와 월 dialog, 본문 16px·보조/표 최소 14px, manifest 기반 iframe 없는 보고서 화면을 구현했습니다.
- 인쇄용 HTML도 공통 `report.css`와 자체 포함 Pretendard/OFL로 교체했습니다. 기존 보고서는 보존하고 새 UUID로 생성했습니다. 과거 `all`의 합성-only 스냅샷과 현재 혼합 스냅샷 차이는 [비교 근거](../benchmarks/workspace-20261023.md)에 명시합니다.
- 첫 axe 검사에서 dl 구조 위반을 발견해 dd 내부로 설명을 옮겼고 최종 재검사23회 위반0입니다. 실제 보고서 선택창 Home/End/Enter·popover ARIA 연결도 확인했습니다. PDF 페이지 나눔과 실기기/스크린리더는 미검증입니다.

## 최종 검수·패키징·문서

- UI UX Pro Max 탐색 위계, Impeccable detector/별도 finish review, Agent Browser, Web Design Guidelines를 적용했습니다. detector64항목의 해석은 benchmark에 기록했고 최종 UI review는 `ship`입니다. malformed admin full-page 캡처는 제외하고 정상 viewport/상세 증거로 검수했습니다.
- Python126/6, Ruff69파일, JS4파일 문법, wheel 및 admin/폰트/OFL/report.css 포함 확인. 문서 검사424개 링크·55개 스크립트·원본8개 checksum 통과(최종 추가 문서 전).
- README·기술 근거·운영 on/off·스킬 목적·최신 이미지·현재 상태를 갱신했습니다. DPR2원본을 재샘플링 없이 크롭하고24개 PNG에 출처 metadata를 넣었습니다.
- Compose dashboard만 `solarops-worker:0.4.1-workspace-20261023`로 재빌드/교체했습니다. 이미지 SHA는 [목록](../image-versions.json)에 보존하며 안정 worker/Airflow 태그와 원본 자료는 유지했습니다.
- 전달 시점에는 기본3서비스·SolarOps kind·별도 관리 서버8504가 실행 중입니다. Compose Airflow는 중지 상태입니다. GitHub 게시/원격CI 결과는 아래 전달 기록으로 추가합니다.

## 전달 준비

- 별도 documenter가 DESIGN.md와 schemaVersion2 sidecar를 최종 소스의 사이드바·16/14px·선택창·보고서·관리 구성으로 갱신했습니다. 현재436개 문서 링크·55개 스크립트·8개 원본 checksum 검사를 통과했습니다.
- 실행 서버의 CSS/JS/report.css/favicon6개와 소스의 SHA가 모두 일치합니다. 최종 이미지ID는 `f93d0fa683f1…`이며 Compose기본3개·kind·관리8504응답을 확인했습니다.
- Git diff whitespace 검사를 통과했고 OFL은 원문의 공백까지 보존하도록 gitattributes로 제한했습니다. 데이터/secret/도구 바이너리는 게시 대상에서 제외했습니다. 검사용 Agent Browser세션은 종료했습니다.
