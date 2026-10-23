# 2026-10-23 — Fable·Astra 모의 면접관 독립 평가

[날짜 목차](2026-10-23.md) · [종합 판단·재현·후속 순서](../reviews/2026-10-23-interview.md) · [handoff](../../handoff.md)

## 목적과 수행 범위

- 사용자 요청으로 신입·주니어 데이터 엔지니어 채용 관점에서 두 독립 평가를 받았습니다. 같은 기준 HEAD `66d63486722dfb7bc83418667c90db1cecfadbf6`와 공통 100점 루브릭을 제공했습니다.
- Astra는 `gpt-6-astra` 독립 에이전트입니다. Fable은 사용자가 안내한 Claude Code로 실행했고 실제 모델 `claude-fable-5-1`을 init·응답에서 확인했습니다. 두 평가자의 결과를 서로 제공하지 않았습니다.
- [Astra 83점](../reviews/2026-10-23-interview-astra.md), [Fable 77점](../reviews/2026-10-23-interview-fable.md). 모두 주니어 면접 권고, 중급은 이 저장소만으로 보류했습니다. 점수는 주관적이며 완성도·합격 확률로 바꾸지 않습니다.
- 평가와 근거 정리만 수행했습니다. 앱 소스·서비스·스케줄·실제 데이터는 변경하지 않았습니다. 과거 기술 검토를 Fable 평가로 바꿔 부르지 않았습니다.

## Claude Code 호출과 원문 보존

- CLI `C:/Users/Taeyang/.local/bin/claude.exe`, 버전 `2.1.287`. `--help`에서 `fable` 별칭·읽기 전용 도구 제한을 확인했습니다. 기존 인증을 사용했고 자격 증명 파일은 읽거나 출력하지 않았습니다.
- 새 세션 `2c9f8b53-0a1e-4630-a410-8a9ee5e83efb`, 결과 success, exit 0, permission denial 0. 93회 도구 호출은 Read/Glob/Grep뿐입니다. 실제 모델·원문 해시는 [근거 JSON](../reviews/2026-10-23-interview-evidence.json)에 있습니다.
- `artifacts/interview-review-20261023/`에 요청문, Fable stream/stderr/원문, Astra 원문·provenance를 보존했습니다. 원시 스트림은 Git에 올리지 않습니다. 평가 전문은 별도 문서로 보존하고 Astra의 로컬 링크를 기준 커밋 링크로 변환하고 줄 끝 공백을 정리했습니다.
- 새 세션에 이전 대화 전체나 상대 평가를 넣지 않았습니다. 모델 접근을 위해 추가 서비스 가입·구매·플러그인 설치를 하지 않았습니다.

주요 호출 형태(요청문은 저장한 UTF-8 텍스트를 stdin으로 전달):

```powershell
$reviewPrompt | & 'C:\Users\Taeyang\.local\bin\claude.exe' -p --model fable `
  --name 'SolarOps Fable independent interview' --output-format stream-json --verbose `
  --tools 'Read,Glob,Grep' --allowedTools 'Read,Glob,Grep' `
  --permission-mode dontAsk --permission-prompts none --strict-mcp-config --safe-mode `
  --no-session-persistence --disable-slash-commands --no-chrome `
  1> artifacts/interview-review-20261023/fable-stream.jsonl `
  2> artifacts/interview-review-20261023/fable-stderr.log
```

## 검사·교차 확인

- Astra는 기존 `test_golden_energy_duplicates_and_missing`, `test_offsets_are_utc`, `test_dst_denominator`를 `python -B -c`에서 직접 호출해 3개 통과했습니다. Fable은 정적 검토만 수행했습니다.
- 본 세션은 일회성 `artifacts/interview-review-20261023/coordinator-checks.py`로 실제 ingest/build_report 및 mock HTTP 응답의 ONS 실패 기록을 실행했습니다. 격리 SQLite·로컬 파일만 사용하며 원본·실행 서비스는 건드리지 않았습니다.
- 시간대 없는 구간 밖 행이 포함된 합성 입력은 기대 50/관측 2/누락 48, 그 행을 제외한 대조 입력은 기대 2/관측 2/누락 0입니다. 전체 누락일 보고서는 보간율 0이지만 일별·overview는 null입니다. 서로 다른 ONS 오류 두 개는 모두 ValueError로 저장됩니다.
- 평가자의 “보고서 실질 영향 없음”은 관측 분모 0의 재현으로 보완했습니다. S3 바이트를 파일 읽기 비용으로 해석하지 않았고, 기존 benchmark JSON이 공유된다는 점도 함께 기록했습니다. 공개 원본에서 결함 조건이 실제 발생했는지는 검사하지 않았습니다.
- 재현 스크립트·합성 산출물은 Git 제외 artifacts에 보존하고 작은 결과 JSON만 커밋합니다. 새 영구 회귀 테스트나 검사 스크립트는 만들지 않았습니다.

실행 명령:

```powershell
.\.venv\Scripts\python.exe -B artifacts/interview-review-20261023/coordinator-checks.py
.\.venv\Scripts\python.exe -B scripts/validation/check_docs.py
git diff --check
gh repo view --json nameWithOwner,visibility
gh run view 39916721418 --json status,conclusion,url,headSha
```

## 수용 판단과 다음 작업

- 새 근거가 있는 INT-01(21점) 시각 계약, INT-02(19점) 보고서 unknown, INT-03(16점) ONS 오류 코드만 [plan](../../plan.md)에 추가했습니다. 이 순서로 수정하되 이번 요청에서는 평가와 계획 등록까지 완료했습니다.
- 기존 PORT-01~04 완료를 취소하지 않지만, 새 결함 발견 후 현재 미완료 기술 항목이 없다고 표현하지 않습니다. 제출 체크리스트 100%와 무결점은 구별합니다.
- 스키마 migration·장기 보존·경보·교차 호스트 복구·반복 성능시험은 운영 요구가 정해질 때 별도 범위로 검토합니다. Kafka/Spark·영업·공개 서비스 배포를 새 완료 조건에 넣지 않았습니다.
- 기존 README는 평가 링크만 추가했습니다. 큰 가독성 개편은 수행하지 않았습니다. 문서·plan·handoff에 이번 평가의 상태와 근거를 연결했습니다.

## 전달 검증

- 기준 HEAD의 [CI 39916721418](https://github.com/TaeyanG4/solarops-audit/actions/runs/39916721418)는 success, 저장소 PRIVATE를 조회했습니다. 과거 CI를 이번 평가에서 재실행한 것으로 표현하지 않습니다.
- 문서 검사: 로컬 링크 812개·스크립트 참조 83개·원본 기획 checksum 8개 통과, `git diff --check` 통과. handoff 42줄·최근 요약 8개와 평가 전문의 본문 일치(링크·줄 끝 공백 변환 제외)를 확인했습니다. 합성 보고서 HTML의 보간율 0.00%도 직접 확인했습니다.
- 변경은 평가 문서·근거 JSON·README 링크·계획·작업 기록뿐입니다. 앱 버전과 릴리스는 v0.5.1 그대로이며 전체 테스트를 불필요하게 재실행하지 않았습니다.
