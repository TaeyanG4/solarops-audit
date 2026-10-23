# 2026-10-23 — 개선 계획과 실행 이력 탐색

[날짜 목차](2026-10-23.md) · [현재 계획](../../plan.md) · [인계](../../handoff.md)

## 우선순위와 범위

- 다음 개선 후보를 영향·확인 가치·확신·후속 해소·범위 보완·비용으로 평가했습니다. OPS-06은 21점(3/2/3/3/3/1)으로 먼저 처리했습니다.
- 기존 `/api/v1/runs`의 발전소 필터를 화면에 연결하고, 메모리에만 있던 상태·페이지·상세 선택을 주소로 복원하는 것이 이번 완료 범위입니다.
- 완료 항목은 plan에서 제거했습니다. 다음은 등록 자료 기간 안내20점, 보고서 스냅샷 설명18점, 읽기 전용 진단18점, 조회 비용 측정17점입니다. 고객 검증16점은 승인된 대상·자료가 없어 보류합니다.

## 변경과 화면

- 정확한 발전소 ID 조회·Enter 제출·필터 초기화, `level/status/run_plant/offset/run` URL 복원, 새로고침·뒤로/앞으로 가기를 추가했습니다. 잘못된 주소는 기본값, 범위를 벗어난 페이지는 마지막 유효 페이지로 정규화합니다.
- 상세 보기·하위 날짜·상위 작업을 실제 링크로 연결했습니다. 실행 이력은 전체 기간의 공개·합성 기록이며 요약 건수는 상태 필터 적용 전임을 표시합니다. 과거 완료와 현재 활성 결과를 혼동하던 설명도 정리했습니다.
- API·계산·출처 의미·CSS는 유지했습니다. [디자인 계약](../../DESIGN.md#run-history), [운영 안내](../runbooks/operator.md), [스킬의 실제 역할](../development/skills.md#실행-이력-탐색-보완--2026-10-23)을 갱신했습니다.
- [실제 데스크톱·모바일 캡처와 출처](../portfolio/images/run-navigation-20261023/README.md): DEMO_01의 **합성 장애 주입 시험 이력**입니다. 공개 발전소의 실제 장애나 운영 성과가 아닙니다.

## 실행한 검사와 한계

- `uv run pytest -q tests/test_workspace.py --junitxml=artifacts/run-navigation-20261023/pytest.xml`: 기존 관련 검사 **5개 통과**. `node --check src/solarops/api/static/dashboard.js`, `git diff --check` 통과. 영구 테스트·전용 검증 스크립트 추가는 **0개**입니다.
- Agent Browser 단발성 확인74명령: 발전소/상태 필터, 상세 새로고침, 하위→상위→뒤로, PS_001 페이지20→40→뒤로/앞으로/새로고침, 빈 결과·초기화·잘못된 URL을 확인했습니다. 1440/768/390px 문서 가로 넘침0, 모바일 axe1회 위반0, 페이지 JS오류0이며 세 너비 이미지를 육안 검토했습니다.
- 원본 명령 응답·검사 요약·JUnit·캡처는 Git 제외 `artifacts/run-navigation-20261023/`에 보존합니다. PowerShell 브라우저 shim이 멈춰 해당 작업의 pwsh만 종료하고 native CLI로 확인했습니다. 검사 세션은 종료했습니다.
- 실제 스마트폰·스크린리더·다른 브라우저·장기 조회 성능은 이번 확인 범위가 아닙니다. 전체 공개 재처리·서비스 시작/중지·전체 로컬 pytest는 반복하지 않았습니다.

## 로컬 반영과 전달

- dashboard JS 캐시 키와 Compose 이미지 태그를 `run-navigation-20261023`으로 갱신하고 dashboard만 빌드·재생성했습니다. DB·MinIO·kind 데이터는 유지했습니다.
- 이미지 ID는 `sha256:84648047dcc3513cbfd896d93d51f7d1e0bba46141f088dcb323bc1fe7ecb384`이며 [버전 기록](../image-versions.json)에 추가했습니다. 로컬 `/ready`는 `ready`입니다.
- `uv run python scripts/validation/check_docs.py`: 로컬 링크536개·스크립트 참조58개·원본 기획 체크섬8개 통과. `git diff --check` 통과, handoff는 100줄·최근 요약8개 이내입니다. 기존 커밋의 전체 CI를 이번 변경의 결과로 간주하지 않습니다.
