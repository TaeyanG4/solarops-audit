# SolarOps Audit — 현재 상태와 재개 지점

기준: 2026-10-24 (Asia/Seoul). 상세 변경·명령·검사·한계는 [날짜별 기록](docs/worklog/README.md)에 둡니다.

## 현재 상태

- **프로젝트 마무리(2026-10-23 사용자 요청).** 마지막 릴리스 v0.5.7(태그 `v0.5.7` = 이미지 빌드 커밋 `4700c65`), 실행 가능한 계획 없음. **10-24 로컬 실행 환경 삭제(사용자 요청)**: 원본 자료와 코드만 남았습니다. 다시 시작할 때는 아래 재개 지점을 따릅니다.

- 최신 릴리스 **v0.5.7 / energy-interval-v2**, 선언 커밋 `4700c65`, Compose 대시보드·kind Airflow/KPO 배포 완료(22:00 KST 전후). [검사·배포](docs/benchmarks/quality-v0.5.7.md) · [릴리스·이미지](docs/releases/0.5.7.json) · [공개 GitHub](https://github.com/TaeyanG4/solarops-audit)(10-23 사용자 요청으로 공개 전환, 이력 비밀값 검사 통과).
- **독립 평가 반복 종료**(사용자 요청, 10-23): R5 Astra 96/Fable 94, R6 Fable 91(지적 5건 0.5.7 보완), R7은 시작 직후 중단해 점수 없음. [R6 판단](docs/reviews/2026-10-23-artifact-r6.md) · [종료·릴리스 기록](docs/worklog/2026-10-23-release-0.5.7.md).
- **10-24 정리(사용자 요청, 원본 자료만 보존)**: 정리 전 SolarOps 약 52GB(폴더 12GB·Docker 40GB). kind 클러스터 `solarops`(노드 볼륨 28.9GB, 그중 27GB는 kind 안에 쌓인 옛 이미지), Compose 컨테이너 8개·볼륨 5개·네트워크, SolarOps 이미지 5개(airflow·worker·minio·kindest/node·postgres), 빈 검증 네트워크 2개, 폴더의 `artifacts/`·`.venv`·`.venv-linux`·`.tools`·`data/`의 처리 결과·복원본·로그를 지웠습니다. 남은 것: `data/raw`·`data/source`(BR-PVGen 원본 ZIP·manifest)·`data/fixtures`(합성 입력 93KB)·코드·문서·`.env`, 폴더 3.2GB. 다른 프로젝트(codex-lb·kaggle-top-solutions)는 그대로입니다.
- 따라서 Compose·kind에 있던 처리 결과(공개 BR-PVGen 51발전소/12,572일 v2, ONS 수집분 Compose 69,696행/21일·kind 167,424행/51일)와 ONS 정기 수집 이력·Airflow 기록은 없어졌습니다. 숫자 근거는 [수집 근거](docs/benchmarks/incremental-v0.5.0.md)·[0.5.7 검사](docs/benchmarks/quality-v0.5.7.md)에 기록으로만 남습니다. Git 제외였던 평가 고정 사본·검증 산출물(`artifacts/`)도 함께 삭제했고 판단 기록은 `docs/reviews/`에 있습니다.
- Docker Desktop 디스크 파일 `docker_data.vhdx`는 110GB 그대로입니다(안의 내용 약 2GB). 압축은 사용자 결정으로 나중에 합니다. Docker Desktop을 끄면 codex-lb도 멈춥니다.
- 다시 켜기: [새 PC 가이드](docs/guides/new-pc.md) 3~5절대로 `uv sync --frozen` → `make up-local`(Compose·Airflow·ONS) → `bash scripts/ops/install-k8s-tools.sh` → `make k8s-bootstrap`·`k8s-deploy`·`k8s-smoke`(kind+KPO). 공개 원본 전체 처리는 6절이며 받아 둔 원본 ZIP은 `data/source`에 남아 있습니다. 랜딩은 `python -m http.server 8507 --bind 127.0.0.1 --directory landing`.
- 추정 kWh·검토 후보·누락/무효/보간을 구분합니다. ONS 원문 MWmed·시간 기준 미확정을 보존하고 기존 kWh에 합산하지 않습니다. 고객·매출·외부 SLO·장기 쓰기 부하는 미검증입니다.
- [독립 랜딩 v6](http://127.0.0.1:8507/) 완료. 히어로 카드를 실제 공개 집계 기반 데모 창(전체 현황/월간 보고서/원본 계보)으로 교체, 보고서 문서형·계보 4단계 흐름, CSS 재작성. 1440/768/375 렌더·axe위반0, 미검증 범위는 [작업 기록](docs/worklog/2026-10-23-landing.md#v6-히어로-실제-데모-창과-전체-다듬기)·[QA](landing/QA.md). [실행](landing/README.md). 별도 loopback 정적 서버이며 FastAPI는 이 작업에서 변경하지 않았습니다.

- **Fornax 견본실 등록(10-24)**: [소개](https://fornaxworks.com/solar.html) · [대시보드](https://fornaxworks.com/solar-app.html) · [시스템 관리](https://fornaxworks.com/solar-admin.html). 실제 프런트엔드에 기록한 응답만 답하는 서버 없는 견본이며, 시작·중지는 아무것도 바꾸지 않습니다. GitHub 프로필 README Projects·Showroom(12칸)도 갱신. 관리 상태 기록 뒤 로컬 서비스는 다시 모두 중지. [기록](docs/worklog/2026-10-24.md).
- **새 머신 전체 재현 검증 통과(10-23)**: README 명령 그대로 Compose·Airflow·kind+KPO·ONS 수집까지 빈 Ubuntu 머신에서 성공([실행](https://github.com/TaeyanG4/solarops-audit/actions/runs/39965762056), 수동/태그 workflow `reproduce.yaml`). 포맷한 PC는 [새 PC 가이드](docs/guides/new-pc.md).

## 다음 재개 지점

1. AGENTS.md → 이 문서 → [plan.md](plan.md)를 읽습니다. 현재 실행 가능한 미완료 항목은 없고 BIZ-01은 사용자 요청으로 보류입니다.
2. 독립 평가는 종료했습니다. 다시 요청받으면 R6 방식(고정 커밋 사본·같은 prompt, Git 제외 `artifacts/artifact-review-r6-20261023/`였으나 10-24에 삭제, 새로 만들어야 함)으로 실행하고, 평가자 사용량 문제는 AGENTS 규칙대로 일시중지합니다.
3. 10-23 Docker 정리(사용자 승인): 검증용 컨테이너 74개·옛 SolarOps 이미지 태그 41개·빌드 캐시 전부 삭제(약 99.7GB). 고아 검증 볼륨 23개(1.39GB)도 삭제. 10-24에는 남은 SolarOps 컨테이너·이미지·볼륨·kind까지 모두 지웠습니다(위 현재 상태). 남은 사용자 결정: 코드 라이선스, GitHub topics, 랜딩 이전 캡처 19장.
4. 릴리스는 `release.json` 변경 → `release.py sync` → `uv lock` → `check` → 구현 커밋 → `build` → Compose `up -d --no-deps dashboard` → WSL `bash scripts/ops/k8s-refresh.sh`. 계산 버전이 바뀌면 과거 결과를 소급 변경하지 않습니다.
5. 현재 로컬 실행 환경은 없습니다(위 다시 켜기 참고). 다시 만든 뒤 kind를 멈추면 ONS 정기 수집도 멈추고, ONS만 멈추려면 DAG pause. 원본 `data/raw`·`data/source` 보존, 민감한 삭제는 사용자 허락이 필요합니다.
6. 단발성·낮은 영향 수정은 기존 검사/화면 확인 우선. UI 변경은 [디자인](DESIGN.md)·[탐색계약](docs/design/workspace-navigation.md), 랜딩은 [landing/DESIGN.md](landing/DESIGN.md) 기준입니다.

## 최근 수행 요약

| 일자 | 수행 영역과 결과 | 상세 |
|---|---|---|
| 10-24 | Fornax 견본실 SOLAROPS 등록·대시보드/시스템 관리 프런트엔드 견본·GitHub 프로필 갱신·로컬 실행 환경 삭제(원본만 보존) | [견본·프로필](docs/worklog/2026-10-24.md) |
| 10-23 | 평가 반복 종료·0.5.7 배포·저장소 점검·README 최신화·서비스 중지·프로젝트 마무리 | [종료·릴리스·점검](docs/worklog/2026-10-23-release-0.5.7.md) |
| 10-23 | 랜딩 v6 히어로 데모 창·보고서/계보 재구성, v5 HTML/SVG 제품 화면·세너비 검수 | [랜딩 구현·검수](docs/worklog/2026-10-23-landing.md) |
| 10-23 | R5 Astra 96 / Fable 94·원문 보존·hash 설명 정정·다음 세션 인계 | [인계·검증](docs/worklog/2026-10-23-handoff-r5.md), [R4 구현](docs/worklog/2026-10-23-quality-r5.md) |
| 10-23 | Fable·Astra 면접 평가·합성 경계 3개 재현·후속 21/19/16점 등록 | [평가·재현·전달](docs/worklog/2026-10-23-interview.md) |
| 10-23 | PORT-01~04완료·ONS상태UI·0.5.1배포·격리재현·제출자료·최신CI | [최종 수행](docs/worklog/2026-10-23-portfolio-finish.md) |
| 10-23 | ONS 실제 증분·정기 KPO·공개 DAG 동시 2개 비교, 0.5.0 배포·문서 갱신 | [수행·전달](docs/worklog/2026-10-23-incremental.md) |
| 10-23 | 입력/게시 4경계 수정·0.4.2 정렬·실제 KPO 재시도/추적·세 환경 7일 일치 | [구현·배포](docs/worklog/2026-10-23-integrity-delivery.md) |

100줄 이내·최근 요약 최대 8개. 이전 handoff/discoveries는 [원문 보관](docs/worklog/archive/README.md)이며 현재 지침이 아닙니다.
