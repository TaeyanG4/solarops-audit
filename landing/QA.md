# Landing v5 verification — 2026-10-23

> **v6 update (same day).** The hero report card was replaced by a three-view demo window (overview, PS_001 report, lineage) using the same saved public data plus `report-metrics.csv`. Executed: Chromium 1440/768/375px renders, no horizontal overflow or console errors, view tabs by click and Arrow/Home/End, unit toggle, date End→Enter, quality metric switch, CSV fetch, axe-core 4.10.2 (0 violations after replacing a nested `aside`; contrast incomplete over the photograph). Not re-run for v6: 320/1920px, no-JS, reduced motion, Taste/Impeccable detectors, device/screen-reader/Safari. Details: [work log](../docs/worklog/2026-10-23-landing.md#v6-히어로-실제-데모-창과-전체-다듬기). The v5 notes below remain the record for earlier checks.

This is the current user-directed revision. Earlier v1–v4 captures and assessments are historical evidence, not the current specification or evidence of user approval. The standalone landing work did not modify the FastAPI application.

## Current composition

- Self-hosted Pretendard, a full-width landscape hero, one enlarged report panel and quiet corner attribution. Actual Channel Talk and flex pages both rendered Pretendard; official Pretendard, SUIT and Wanted Sans descriptions informed the choice.
- Product fragments are editable HTML/SVG using saved public aggregates. The background photograph is the only displayed raster; the source screenshot remains available through **전체 캡처 확대**. Nested presentation frames and repetitive capture/preview captions were removed.
- Three historical statistics share one hierarchy: 51 plants, approximately 14.4 million inverter rows and 12,572 published day partitions. Their scope differs from the five-plant April overview and single-plant PS_001 report.
- The date listbox uses opaque navy, gold selection and a thin matching scrollbar. Page, table and code scrollbars share the slate palette. Mobile scope notes, chart instructions and tooltips are at least 13px.
- No entry or scroll-triggered panel motion. Short local feedback follows deliberate interactions; reduced motion suppresses it. No simulated live data.

## Executed checks

| Check | Result and evidence |
|---|---|
| Final Chromium rendering | Full page and first fold at 1440 / 768 / 390px; panels, typography, spacing and date popup inspected. `v5-final-layout.json`: no horizontal overflow or page exceptions; metric-result heights identical across states. |
| Additional responsive checks | 320 / 390 / 720 / 768 / 1024 / 1440 / 1920px passed overflow, image/font loading and heading-wrap checks. `v5-extra-checks.json` predates final statistics/date refinements; final three-width captures include them. Final focused 320px check: document width 320px, Pretendard loaded, mobile notes 13px. Cold-load CLS observed 0–0.0183, not universally zero. |
| Chart and dates | All 30 dates matched saved values. Hover, bar activation, arrows, Home/End, previous/next and first/last boundaries checked. `interaction-v5.json`. |
| Date listbox | Real keyboard End → Enter selected April 30 / 60.13 MWh and closed; Escape and focus return checked. Current DOM has exactly one `#day-options`, controlled by `#day-trigger`. Current desktop/mobile popup captures saved locally. |
| Other interactions | kWh/MWh, both quality-control groups, HTML/CSV/JSON tabs, disclosures and stable result heights checked on desktop, mobile and reduced-motion runs. Actual browser click copied the manifest hash; without clipboard access, selectable fallback worked. |
| Entry and scroll motion | Instrumented WAAPI calls: 0 on entry and across page scrolling at 1440 / 390px. `motion-v5.json`. Deliberate interaction feedback remains. |
| No JavaScript / reduced motion | Static figures, chart, table, report, links and native disclosures remain available; enhancement buttons disabled without JavaScript. Reduced-motion interaction run: no animations or overflow. |
| axe 4.12.1 | Landing desktop/tablet/mobile: 0 violations. Initial v5 runs had 1 incomplete category; final mobile and open-listbox checks had 2. Evidence page desktop/mobile: 0 violations / 0 incomplete. |
| Saved data and local assets | Inline `#preview-data` matches `assets/data/preview.json`. Monthly and daily precision retained, including 0.002 kWh rounding difference. 43 local references/anchors/HTTP assets: no errors; JS syntax and diff checks passed. Repository docs: 972 local links, 110 script references, 8 archived checksums passed. |
| Taste checks | Source lint: 0 FAIL / 0 WARN. Three-width current inspector: 0 FAIL / 4 WARN before the mobile 13px adjustment. Focused final mobile run: 0 FAIL / 1 WARN (type-size count); small-text warning resolved. |
| Impeccable review | Targeted detector: no findings after two scoped false-positive exceptions. Fresh independent reviewer inspected source, design and six v5 captures: `ship`, no material fixes. The later 1px mobile adjustment received a focused rendered check. |

## Accessibility and detector limits

The two axe incomplete categories are **photographic pseudo-element contrast** and **inability to resolve the listbox's aria-controls relationship**. They are not zero-incomplete passes. The real ID relationship was verified in the DOM and with keyboard interaction; screen-reader operation was not tested.

Pixel-backed checks of header, hero heading, lead and photo credit measured a minimum **7.36:1** across 320 / 390 / 768 / 1440 / 1920px (`contrast-v5-results.json`). These sampled regions do not certify every state. Opaque report panels retain navy backgrounds. Obsolete caption measurements were removed from the current record.

Impeccable's `cramped-padding=*` and `low-contrast=*` exceptions apply **only to landing/index.html**. The former misses centered inner wrappers: final measured gutters are 20px at 390px and 80px at 1440px (`hook-insets-v5-final.json`). The latter associates white hero text with the light body canvas incorrectly. Shared `.impeccable/config.json` records reasons and measurement files. Earlier v2 inset measurements remain historical evidence. Recheck when section spacing or hero backgrounds change; axe and rendered review remain enabled.

Taste inspector uses `--allow still-page,picture-count,eyebrow`: stationary content and native product UI follow explicit user feedback; its eyebrow heuristic associated the quiet photo credit with statistics. Media warnings concern one photograph and no footage. The type-size warning includes marketing hierarchy and product data/control sizes. No unrelated decoration was added. Final mobile record: `inspect-v5-mobile-final/report.json`; preceding three-width record: `inspect-v5-current/report.json`.

## Current render evidence

- [Desktop full page](../docs/portfolio/images/landing-20261023/desktop-v5.png) · [first fold](../docs/portfolio/images/landing-20261023/desktop-fold-v5.png)
- [Tablet full page](../docs/portfolio/images/landing-20261023/tablet-v5.png) · [first fold](../docs/portfolio/images/landing-20261023/tablet-fold-v5.png)
- [Mobile full page](../docs/portfolio/images/landing-20261023/mobile-v5.png) · [first fold](../docs/portfolio/images/landing-20261023/mobile-fold-v5.png)
- [Design and tokens](DESIGN.md) · [asset provenance](assets/images/README.md) · [implementation and commands](../docs/worklog/2026-10-23-landing.md)

Detailed local evidence: Git-excluded `artifacts/landing-20261023/`, including `v5-final-layout.json`, `v5-extra-checks.json`, `interaction-v5.json`, `motion-v5.json`, `axe-v5-*.json`, `contrast-v5-results.json`, `links-v5.json`, inspector reports and `date-picker-v5-{desktop,mobile}.png`. Original images, saved API/manifest values and rejected intermediate captures are preserved.

Physical phones, screen readers, Safari, real traffic, commercial conversion and external SLO were not tested. This landing uses a saved public-data snapshot and does not connect to the backend. No permanent regression suite or project runtime dependency was added for this UI refinement.
