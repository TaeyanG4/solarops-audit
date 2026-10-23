# Fable R3 실행 정보

- Claude Code2.1.287, 실제모델 `claude-fable-5-1`, 세션 `04c17666-dba3-450e-840a-9a8ac6384f2c`.
- 대상36ac6ff937b06a481988d9264c65ac1a9597a59a. Read/Glob/Grep/Bash, 지정집중79검사24.50초·새합성7일데모·release check통과. 로그490events와prompt는 Git제외 artifacts/artifact-review-r3-20261023에 보존.
- 최초 호출에 테스트 파일명 오타가 있어 점수 생성 전에 해당 자식 프로세스만 종료하고 실제 `test_calculation_v2.py`로 정정한 새 세션을 실행했습니다. 중단 stream도 보존했고 유리한 점수를 고르기 위한 재호출이 아닙니다.
- 목표·이전점수·상대평가 비공개. plan/handoff/과거평가 제외. 코드·검사는 대상커밋과 같으나 별도 랜딩 작업의 README소개2줄이 작업트리에 추가된 상태로 읽혔습니다. 원문도 이를 명시했고 동선감점에 랜딩을 언급했으므로 문서까지 완전히 고정된 비교라고 주장하지 않습니다.
- 다음 평가부터 허용된 tracked파일을 커밋archive에서 새 별도 폴더로 추출하고 해당 src를 Python경로로 고정합니다. 점수 원문은 수정하지 않습니다.
