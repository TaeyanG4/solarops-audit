# ONS 시간별 발전 수집 계약

ONS의 [Geração por Usina em Base Horária](https://dados.ons.org.br/dataset/geracao-usina-2)를 수집합니다. [CKAN metadata](https://dados.ons.org.br/api/3/action/package_show?id=geracao-usina-2), [공식 데이터 사전](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.pdf)(2023-06-09), 실제 CSV를 함께 확인했습니다.

## 원천과 의미

| 항목 | 보존·해석 방식 |
|---|---|
| 공급자·라이선스 | ONS, metadata의 `cc-by`, Creative Commons Atribuição. 링크는 `http://www.opendefinition.org/licenses/cc-by`; 버전은 명시되지 않아 4.0이라고 쓰지 않음 |
| 원천 시간 | `din_instante`, 매시 정각 문자열. 사전에 시간대·구간 시작/끝 정의가 없어 `source_time` 그대로, `ts_utc=null` |
| 발전 값 | `val_geracao`, 단위 **MWmed**. 원천 시간별 평균 발전 값; kWh로 변환하거나 기존 추정 에너지에 합산하지 않음 |
| `verified` | TIPO I/II-A/II-B/II-C, Conjunto de Usinas. ONS 설명상 검증 발전 자료이며 현장 계량기 보증을 뜻하지 않음 |
| `forecast` | Pequenas Usinas (Tipo III). 공식 설명에 예측 발전이라고 명시 |
| `unspecified` | MMGD 및 알려지지 않은 모드. 실측·예측을 추측하지 않음 |
| 식별자 | `id_ons`가 있으면 그 값의 hash, 없으면 지역/운영모드/원문명/CEG 복합 hash. 그룹을 개별 발전소라고 표시하지 않음 |
| 보간·표본 수 | 원천 미제공. false·0으로 채우지 않음 |
| 무효·누락 | 음수/빈값/비수치/무한값은 `valid=false`, 값 null, 원문 문자열 보존. 해당 날짜에 존재한 entity의 24개 **시각 라벨** 대비 누락만 집계; DST나 전체 발전소 커버리지 추정이 아님 |

2026-10-23에 확인한 파일은 10월1~21일, 전체365,040행 중 태양광69,696행입니다. 이것은 BR-PVGen의51개 발전소 또는15분 인버터 관측과 다른 데이터입니다. 원천 공개 후에도 정정될 수 있습니다.

## 수집과 원자 게시

1. 월별 metadata에서 공식 CSV URL·라이선스 ID를 확인합니다. 임의 URL을 CLI에 받지 않습니다.
2. 이전 **성공** cursor의 ETag로 조건부 GET합니다. 다운로드는 월별256MiB 상한이며 partial/잘린 응답은 거부합니다. multipart ETag를 MD5로 쓰지 않고 별도 SHA-256을 계산합니다.
3. 원본 CSV와 CKAN metadata를 조직별 immutable raw로 보존합니다. 태양광 행의 계약·시각·중복을 검증합니다. 동일 중복은 계수, 충돌 중복은 월 게시를 중단합니다.
4. 날짜별 정렬된 내용·품질·계약 hash를 비교해 변경·추가된 날만 JSON 객체를 업로드합니다. 원천에서 사라진 날짜는 `withdrawn`/0행 manifest로 전환하고 이전 객체는 보존합니다.
5. 이전 cursor의 실행 ID가 여전히 같을 때만 변경 날짜와 새 cursor를 **같은 DB transaction**으로 게시합니다. 실패·경쟁에서 진 작업은 이전 성공 상태를 보존합니다. upload 후 DB 실패로 남은 객체는 미게시 증거로 유지합니다.
6. HTTP304 또는 같은 원본SHA는 재분석하지 않습니다. 확인 이력은 남기되 일별 manifest의 최초 원본 계보·실행ID는 그대로 유지합니다.

`collection_cursor`, `collection_partition`, `collection_run`은 모두 `org_id`로 분리합니다. 기존 BR-PVGen 계산/보고서 테이블을 재사용하지 않습니다. 신규 테이블 때문에 새 read-only API를 띄우기 전에 `db-migrate`가 필요합니다.

## 실행·조회

```text
uv run solarops ons-sync --period 2026-10
uv run solarops ons-sync --as-of 2026-10-23
uv run solarops ons-status --period 2026-10
```

`--period`는2022년 이후 명시한 월 하나를 수집합니다. `--as-of`는 기준일의 이전 월과 현재 월을 순서대로 확인합니다. 둘을 생략하면 실행일(UTC)을 기준으로 합니다. 최대2개월이며 이전 월이 먼저 성공하고 현재 월에서 실패하면 이전 월의 성공은 보존됩니다. 아직 게시되지 않은 당월 파일은 실패로 기록하고 재시도합니다. 두 달보다 오래된 정정은 `--period`로 수집해야 합니다.

- `GET /api/v1/sources/ons?period=2026-10`: 계약·일별 manifest·최근20회 실행.
- `GET /api/v1/sources/ons/days/2026-10-01?offset=0&limit=100`: SHA검증 후 원문 포함 hourly 행, 최대500행/응답.
- 기존 대시보드의 BR-PVGen `public` 필터·차트·보고서에는 합산하지 않습니다. 현재 ONS 조회는 CLI/API이며 별도 화면은 구현하지 않았습니다.

Airflow `solarops_ons_daily`는 매일05:00UTC(14:00KST), `data_interval_end` 날짜의 이전/현재 월을 같은 CLI로 수집합니다. catchup=false, 동시 실행1개, 재시도2회, 생성 시 paused입니다. **정의된 주기와 실제 활성화 여부는 다릅니다.** 현재 실행/배포 근거는 [작업 기록](worklog/2026-10-23-incremental.md)에 기록합니다.

## 검증 범위

기존 계약/게시/서비스 테스트에 작은 offline fixture로 단위·원천 시각·유형·invalid·누락·중복충돌·동일응답·정정/지연/철회·실패 cursor·조직 격리를 추가했습니다. 전체 데이터를 테스트에서 다운로드하지 않습니다. 실제 원천과 성능 결과는 [실행 기록](worklog/2026-10-23-incremental.md)으로 분리합니다.
