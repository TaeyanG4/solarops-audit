# SolarOps Audit landing

FastAPI 대시보드와 분리한 정적 B2B 제품 소개 페이지입니다. HTML/CSS/JavaScript·SVG와 저장된 공개 집계값, 로컬 배경 사진·글꼴을 사용하며 앱 API·데이터베이스 연결, 폼 제출, 추적 스크립트가 없습니다.

## 실행

저장소 루트에서 Python 3.12로 실행합니다. 패키지 설치나 프런트엔드 빌드는 필요하지 않습니다.

```powershell
python -m http.server 8507 --bind 127.0.0.1 --directory landing
```

[랜딩페이지](http://127.0.0.1:8507/) · [검증 근거·실행 안내](http://127.0.0.1:8507/evidence.html). 상단 **로컬 데모 실행**은 같은 PC의 실제 대시보드 `127.0.0.1:8502`(2024-04 공개 전체 현황)를 새 탭으로 엽니다. 대시보드가 꺼져 있으면 열리지 않으므로 [운영 절차](../docs/runbooks/operator.md#8502가-열리지-않을-때)로 시작합니다. 실행 방법 문서는 가운데 메뉴 **실행 안내**입니다. 같은 PC에서 접속하며 종료는 해당 터미널에서 Ctrl+C입니다. 저장소 루트 전체를 HTTP로 제공하지 마세요. `landing/`만 제공하는 위 명령을 사용합니다.

이번 작업의 미리보기는 숨김 Python 프로세스 PID 50104로 시작했습니다. 종료 전 해당 PID의 명령줄이 위 서버인지 확인합니다. 기존 대시보드 8502와 서비스는 독립입니다.

## 구성과 편집

- [index.html](index.html): 제품 소개, 히어로의 3화면 데모 창(전체 현황·월간 보고서·원본 계보, 편집 가능한 HTML·SVG), 품질·보고서 형식·게시 흐름, FAQ.
- [evidence.html](evidence.html): 주장별 검증 범위·한계·출처와 로컬 합성 데모 실행 방법.
- [styles.css](styles.css), [site.js](site.js): 반응형 스타일, 점진적 향상. JavaScript 비활성 시 정적 지표 설명과 기본 링크·FAQ가 유지됩니다.
- [디자인](DESIGN.md), [카피·CRO](COPY.md), [추첨 방향](design-direction.json): 선택 이유·대안·주장 근거.
- [공개 집계 미리보기](assets/data/preview.json), [월간 CSV](assets/data/report-metrics.csv): 실제 공개 API·PS_001 발행 보고서에서 읽은 저장본. 원본 데이터셋이 아닌 월간·일별 집계입니다.
- [이미지 출처](assets/images/README.md), [OFL](assets/fonts/OFL.txt): 자산 출처·캡처 처리 범위.

제품 카피를 바꿀 때 공개 자료·합성 시험·고객 운영을 구분하고 근거 문서를 함께 갱신합니다. `site.js`의 세 지표는 실제 2024년 4월 공개 조회 결과의 설명용 값이며 실시간 API 값이 아닙니다. 실제 고객·매출·고장 정확도·금전적 손실을 주장하지 않습니다.

## 검수

[2026-10-23 작업 기록](../docs/worklog/2026-10-23-landing.md)에 실행 명령, 최종 렌더링, 접근성·상호작용·무스크립트 검사와 한계를 기록합니다. 별도 영구 회귀 테스트나 프로젝트 실행 의존성을 추가하지 않았습니다.

### 제품 화면 편집

제품 화면의 글자·구조는 `index.html`, 색상·크기·스크롤바는 `styles.css`, 마우스·키보드·짧은 전환은 `site.js`에서 바꿉니다. 제품 이미지를 편집할 필요가 없습니다. 사진은 `assets/images/solar-landscape.webp` 하나입니다.

값을 갱신할 때 `assets/data/preview.json`과 HTML의 `#preview-data`, 정적 표시값·SVG·일별 표를 함께 맞춥니다. 기존 값은 2026-10-23에 읽은 공개 2024년 4월 자료입니다. 일별 API 반올림 합계와 월 집계는 0.002 kWh 차이를 그대로 보존했습니다. 출처나 보간 여부를 새로 추측하지 않습니다.

폰트는 현재 문자를 추출한 Pretendard 서브셋입니다. 새로운 한국어 문자를 추가할 때 보존된 `assets/fonts/PretendardVariable.woff2`에서 HTML·JS 문자와 ASCII를 포함하도록 fontTools로 재생성합니다. 원본 글꼴·라이선스는 삭제하지 않습니다.
