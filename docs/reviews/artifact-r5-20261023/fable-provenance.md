# Fable R5 실행 출처 — 수집 세션 기록

2026-10-23 Asia/Seoul. 평가자가 작성한 [최종 원문](fable-review.md)은 수정하지 않았습니다. 이 문서는 원문과 CLI 실행 기록을 대조한 부모 세션의 메타데이터입니다. [기계 판독 근거](evidence.json).

- Claude Code 2.1.287, 요청 `--model fable`, 최종 `modelUsage` 실제 식별자 `claude-fable-5-1`. 세션 `ce4eec59-6435-4c71-827f-f0a03afdba85`, 성공 종료, 143턴/722.466초. 면접·개인 역량·목표 점수·이전 평가를 전달하지 않았습니다.
- 대상 commit `faa6f3baf8e1925ccc21f402419cf1333f2e5010`, 구현 `4b9959e`, 앱0.5.6. 동일 archive의 303개 파일을 별도 `source-fable`에 제공했습니다. 부모가 archive SHA256과 두 사본의 추적 파일 해시를 대조해 변경0을 확인했습니다. 평가자가 archive를 직접 검증했다고 주장하지 않습니다.
- 평가 디렉터리 `artifacts/artifact-review-r5-20261023/source-fable`. 새 .venv에 잠금 의존성을 기존 Python3.12.13/uv/공유 캐시로 설치했습니다. 새 OS는 아니며 공개 자료 전체를 다운로드하지 않았습니다. import 경로는 해당 사본의 src입니다.
- 도구 Read/Glob/Grep/Bash, 명시된 실행 허용 목록·dontAsk·safe-mode·strict MCP·no-session-persistence. 거부8건에는 Ruff/문서 검사와 정확한 허용 명령에서 벗어난 pytest/스크립트 저장 요청이 포함됩니다. 승인 우회 없이 허용된 명령과 일회 Python 명령으로 검증했습니다.
- 전체 JUnit154건 중140통과·14제외(13서비스 opt-in,1호스트 symlink 권한),41.400초. 실제 격리 PostgreSQL/MinIO 13통과,27.139초. 시험 컨테이너2개는 중지·보존했습니다. 실패 게시·재처리·7일 데모와34개 파일 SQLite 복원도 성공했습니다.
- `fable-probe/probe-result.json` 파일은 없습니다. 일부 저장 명령은 거부되었고 추가 확인은 Python `-c`의 도구 출력에 남습니다. 부모가 성공한 도구 결과에서 Parquet 재계산·필드 누락 KeyError를 추출했습니다. 이를 영구 probe 파일이 존재한다고 설명하지 않습니다.

원본 실행기·프롬프트·UTF-16LE stream은 Git 제외 `artifacts/artifact-review-r5-20261023/`에 보존합니다. 최종 응답 문자열만 UTF-8 `fable-review.md`로 추출했고 원문 SHA를 evidence.json에 기록했습니다. 전체 stream은 도구 기록을 포함하므로 Git에 게시하지 않습니다. 공개 수집·KPO·서비스 복원·브라우저의 과거 증거는 이번에 재실행한 결과와 구분합니다.

Git의 Markdown LF 정규화와 원본 바이트를 구분합니다. evidence.json에 로컬 원본 SHA와 Git 저장본 SHA를 각각 기록했으며 평가 내용·점수는 변경하지 않았습니다.
