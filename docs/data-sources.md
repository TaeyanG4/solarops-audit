# 데이터 출처와 해석

[프로젝트 홈](../README.md) · [데이터 계약](data-contract.md) · [설치와 처리](guides/setup.md)

SolarOps에는 **실측 기반 공개 역사 자료**와 **프로젝트가 만든 합성 데모**가 있습니다. 고객 데이터나 실시간 운영 자료는 포함하지 않습니다. 공개 원천도 이미 집계·일부 보간된 자료이므로, 화면의 에너지를 계량기 실측 전력량으로 해석하면 안 됩니다.

2026-10-23에 게시 체크섬과 로컬 원본 4개, 압축 해제 CSV 102개, 공개 계보 103개를 대조하고 대표 하루를 독립 계산했습니다. [파일 동일성·실제 저장소·보고서까지의 확인 결과](benchmarks/stack-authenticity-20261023.md). 이는 파일과 계산 경로의 검증이며 원본 제작자의 현장 계측 정확도 인증은 아닙니다.

## 공개 원천: BR-PVGen

| 항목 | 확인한 내용 |
|---|---|
| 정식 이름 | BR-PVGen — The Brazilian Photovoltaic Generation Dataset |
| 배포 페이지 | [Zenodo record 21511487](https://zenodo.org/records/21511487) |
| DOI / 버전 | [10.5281/zenodo.21511487](https://doi.org/10.5281/zenodo.21511487) / V.1 |
| 제작자 | Caian Dutra de Jesus, Rhuan Nascimento Ferreira, Eduardo Pestana de Aguiar |
| 소속 | Universidade Federal de Juiz de Fora (UFJF), 브라질 |
| 이용 조건 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): 출처·라이선스·변경 사항 표시 |
| 범위 | 브라질 51개 익명 발전소, 2024-03-26~2025-06-09. 발전소별 수록 기간은 다름 |
| 시간 해상도 | 원천 SCADA 약 5분 관측 → 가중 이동 평균으로 15분 집계 → 일부 짧은 공백 보간 |
| 전체 행 수 | 인버터 14,400,480행 / 기상 1,151,232행. 파일 전체 기준이며 유효값 비율과는 별개 |
| 위치 정보 | 익명 발전소 ID와 주 단위 위치. 고객명·정확한 현장 위치를 의미하지 않음 |

2026-10-23에 [Zenodo API](https://zenodo.org/api/records/21511487)와 배포 설명을 확인했습니다. API의 publication_date는 2026-07-23, 원문 Readme의 release 표기는 2026-07-24입니다. 이 배포 날짜 차이는 관측 기간과 무관하며 임의로 하나로 합치지 않았습니다.

## 파일별 역할과 다운로드

| 파일 | 역할 | 배포 크기 | 직접 링크 |
|---|---|---:|---|
| `Readme.txt` | 수집·집계 방식, 컬럼, 범위, 인용 설명 | 10,090 B | [원문](https://zenodo.org/records/21511487/files/Readme.txt?download=1) |
| `BR-PVGen_metadata.csv` | 발전소 ID, 설비·용량 등 메타데이터 | 3,095 B | [CSV](https://zenodo.org/records/21511487/files/BR-PVGen_metadata.csv?download=1) |
| `BR-PVGen_inverter.zip` | 발전소별 인버터 전력·전기 관측 CSV | 약 294 MB | [ZIP](https://zenodo.org/records/21511487/files/BR-PVGen_inverter.zip?download=1) |
| `BR-PVGen_meteorological.zip` | 일사량 등 기상 관측 CSV | 약 57 MB | [ZIP](https://zenodo.org/records/21511487/files/BR-PVGen_meteorological.zip?download=1) |

크기는 10진 MB로 반올림했습니다. 정확한 checksum과 실제 컬럼 계약은 [데이터 계약](data-contract.md)에 있습니다. 원본 CSV·ZIP은 GitHub에 재배포하지 않으며 로컬 `data/source/`에 보관합니다.

저장소 루트에서 실행합니다. 기본 `fetch`는 작은 설명·메타데이터 파일만 받습니다.

```text
uv run solarops source inspect
uv run solarops source fetch
```

전체 공개 자료가 필요한 경우:

```text
uv run solarops source fetch --allow-large --files Readme.txt BR-PVGen_metadata.csv BR-PVGen_inverter.zip BR-PVGen_meteorological.zip
uv run solarops source extract data/source/BR-PVGen_inverter.zip data/source/inverter
uv run solarops source extract data/source/BR-PVGen_meteorological.zip data/source/station
```

다운로드는 분석 결과를 자동 생성하지 않습니다. 환경 설정과 replay·보고서 생성은 [설치 안내](guides/setup.md)를 따릅니다. 다운로드 후 배포 checksum을 확인하고, SHA-256 및 manifest로 수집 근거를 보존합니다.

## 원천에서 화면까지

```mermaid
flowchart LR
    A[Zenodo 공개 ZIP · CSV] --> B[checksum 확인 · 원본 보존]
    B --> C[UTC · 스키마 · 중복 · 값 검증]
    C --> D[일별 Parquet · 품질 지표]
    D --> E[월간 추정 에너지 · 보고서 · 대시보드]
```

SolarOps의 변경은 정규화, 품질 분류, 일별 처리, 추정 에너지 계산과 보고서 생성입니다. 원본의 NULL·보간 표시·집계 표본 수를 보존하며 빈 값을 새로 보간하지 않습니다. 유효 전력에 `W ÷ 1000 × 0.25 h`를 적용한 kWh 합계는 **추정 에너지**입니다. 원천 보간값이 포함될 수 있으며 계량기 실측 전력량이나 매출을 뜻하지 않습니다.

유효·무효·누락은 슬롯 분류입니다. **원본 보간은 이 분류와 겹칠 수 있는 속성**이므로 네 종류를 하나의 합계로 더하지 않습니다. 보간 여부를 알 수 없는 행도 별도로 보존합니다. 등록되지 않은 날짜와 등록된 일별 파티션 내부의 누락 슬롯 역시 구분합니다.

공개 2024년 4월 화면은 자료가 있는 **5개 발전소**를 표시합니다. 전체 데이터셋의 51개와 다른 것은 월 필터 때문입니다. PS_005는 20일만 등록된 부분 기간이며, PS_001의 관측 슬롯 완전성 100%도 유효값 100%를 뜻하지 않습니다.

## 합성 데모

[합성 생성기](../src/solarops/fixtures.py)가 DEMO_01의 기본 1주 자료를 만들고 [실행형 데모](../scripts/demo/portfolio_demo.py)가 정상 처리·실패 주입·재처리·보고서를 재현합니다. 설치 후 `uv run python scripts/demo/portfolio_demo.py --serve`로 실행할 수 있습니다.

합성 자료는 파이프라인 동작을 설명하는 테스트 자료입니다. 실제 발전소 수, 공개 데이터 처리량, 고객 성과에 합산하지 않습니다. 실행 이력의 `INJECTED_DURING_COMMIT`는 복구 검증을 위해 의도적으로 발생시킨 실패이며 현장 장애가 아닙니다.

## 인용과 출처 보존

> De Jesus, C. D., Ferreira, R. N., & de Aguiar, E. P. (2026). *BR-PVGen — The Brazilian Photovoltaic Generation Dataset* (V.1). Zenodo. https://doi.org/10.5281/zenodo.21511487

이 표기는 배포 Readme의 권장 인용을 따릅니다. 관련 IEEE Access 논문은 원문에서 in press로 안내하며 DOI는 제공되지 않아 여기에 추정해 넣지 않았습니다. 이 저장소의 분석·시각화는 SolarOps의 가공 결과입니다.

원문·API 메타데이터·파일별 manifest는 로컬 `data/source/`에, 이번 출처 확인의 요약은 `artifacts/docs-refresh-20261023/source-metadata.json`에 보존했습니다. 로컬 증거 경로는 Git 제외이며, GitHub 독자는 위 배포 URL과 [계약 문서](data-contract.md)로 출처를 확인할 수 있습니다.
