# Copy and conversion decisions

Diagnosis A: a new landing page, with existing technical documentation as the factual source. Voice: a product engineer explaining an operations workflow in plain Korean. Avoid AI, automatic diagnosis, guaranteed savings and customer-success language.

## Locked copy deck

Hero: **태양광 데이터, / 숫자부터 근거까지**

SolarOps Audit는 발전량의 추정치와 데이터 품질을 함께 보여주고, 월간 보고서의 숫자를 원본까지 연결합니다.

Hero badge (v6): **BR-PVGen 공개 자료 · 2024년 4월 실제 집계**. Secondary CTA (v6): **검증 근거 보기** → evidence page; header action **로컬 데모 실행** → local demo instructions.

Primary CTA: **제품 화면 살펴보기** (scrolls to the in-hero demo window). Repeated preview/capture microcopy was removed at the user’s request. Provenance remains in the evidence page.

Quality: **값이 있다는 것과 / 쓸 수 있다는 것**. 같은 2024년 4월 자료도 관측 슬롯은 100%, 유효값은 82.5%입니다. 누락·무효·원본 보간을 구분해야 숫자의 의미가 보입니다.

Reports: **보고할 숫자에 / 근거를 함께**. 추정 발전량, 데이터 품질, 계산 버전을 월간 보고서에 담습니다. HTML로 읽고, CSV와 원본 계보 JSON으로 이어서 검토하세요.

Lineage: **값이 바뀌어도 / 근거는 남도록**. 보고서는 발행 당시의 스냅샷을 보존합니다. 현재 게시 결과와 비교해, 재처리 이후 근거가 달라졌는지 확인할 수 있습니다.

Proof: **확인한 만큼만 / 이야기합니다**. 공개 자료 처리와 합성 실패 시험의 범위·조건을 함께 공개합니다.

Close: **다음 보고서는, / 근거부터 확인하세요**. 실제 화면을 살펴보고, 로컬 데모에서 실패와 재처리 흐름을 재현할 수 있습니다.

FAQ covers estimated kWh, failure candidates, sources, local availability, and verification boundaries. No invented commercial offer.

## Candidates and decisions

- Hero A (selected): 태양광 데이터, 숫자부터 근거까지 — readable at two lines on mobile, specific to source lineage.
- Hero B: 보고서 숫자의 출처를 확인하세요 — concrete but understates solar and quality.
- Hero C: 발전 데이터의 근거를 잇다 — shorter but less direct about the task.
- CTA A (selected): 제품 화면 살펴보기 — names the immediately available next step.
- CTA B: 공개 자료로 둘러보기 — could imply a live connected demo on every host.
- CTA C: 데모 시작하기 — misleading for an in-page screenshot demonstration.

## CRO review

Goal: inspect the product workflow. Traffic source and conversion baseline are unknown. Technical evaluators are an assumed audience; no conversion uplift is claimed.

Implemented: one repeated primary CTA; historical processing scope after the hero; interactive product components adjacent to feature claims; clear source/month captions; thumb-size controls; local demo instructions and repository-access caveat; FAQs answer scope objections. Avoid registration, invented contact destinations and placeholder sales forms.

Future test ideas only: compare the lineage-led headline with a quality-led headline when real traffic and an agreed measurement plan exist. No analytics or tracking installed.

## Current user-directed flow

Public scope: **공개 자료로 확인한 규모** → **51개** BR-PVGen 발전소, **1,440만 행** 인버터 관측 자료, **12,572개** 검증·게시한 일별 파티션. All three are supported by `docs/benchmarks/stack-authenticity-20261023.md`. This is the whole historical dataset, not the monthly five-plant preview or customer count.

Product overview: **월간 발전량과 / 품질을 함께 읽다**. Visitors can inspect dates, change report units/formats, compare quality meanings and open source IDs. These controls explore saved public values; they do not imply a live backend. Quiet credits and evidence links remain secondary. No user conversion result is claimed.
