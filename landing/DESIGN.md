---
name: SolarOps Audit landing
description: A stationary photographic introduction to traceable solar-data evidence.
colors:
  ink: "#172131"
  muted: "#59667a"
  paper: "#f1f3f7"
  white: "#ffffff"
  gold: "#f3ba55"
  inverse-muted: "#c0cbdc"
  green: "#16745e"
  focus: "#285bdd"
  canvas: "#f8fafb"
  hero-foundation: "#111d2c"
  quality-field: "#edf0eb"
  closing: "#f1cc88"
  control-slate: "#26354a"
  menu-slate: "#213047"
  menu-hover: "#344760"
  control-border: "#6b7c92"
  dark-divider: "#344254"
  invalid-ochre: "#965d12"
typography:
  display:
    fontFamily: 'Pretendard, "Malgun Gothic", sans-serif'
    fontSize: "clamp(38px, 4.25vw, 62px)"
    fontWeight: 700
    lineHeight: 1.22
    letterSpacing: "-0.03em"
  headline:
    fontFamily: 'Pretendard, "Malgun Gothic", sans-serif'
    fontSize: "clamp(32px, 3.4vw, 46px)"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  title:
    fontFamily: 'Pretendard, "Segoe UI", "Malgun Gothic", sans-serif'
    fontSize: "24px"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "-0.02em"
  body:
    fontFamily: 'Pretendard, "Segoe UI", "Malgun Gothic", sans-serif'
    fontSize: "18px"
    lineHeight: 1.65
  label:
    fontFamily: 'Pretendard, "Segoe UI", "Malgun Gothic", sans-serif'
    fontSize: "14px"
    lineHeight: 1.6
  metric:
    fontFamily: 'Pretendard, "Segoe UI", "Malgun Gothic", sans-serif'
    fontSize: "clamp(40px, 4vw, 58px)"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  code:
    fontFamily: "Consolas, monospace"
    fontSize: "14px"
    lineHeight: 1.75
rounded:
  option: "6px"
  compact: "8px"
  header: "10px"
  control: "12px"
  panel-small: "16px"
  panel: "20px"
  pill: "100px"
spacing:
  tight: "8px"
  compact: "12px"
  control: "16px"
  mobile: "20px"
  group: "24px"
  panel: "32px"
  wide: "48px"
  section-gap: "64px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "16px 24px"
  button-primary-hover:
    backgroundColor: "#2c3c53"
  button-inverse:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "16px 24px"
  button-inverse-hover:
    backgroundColor: "#e2e6ec"
  navigation:
    textColor: "{colors.white}"
    typography: "{typography.label}"
    padding: "12px 0"
  date-picker:
    backgroundColor: "{colors.control-slate}"
    textColor: "{colors.white}"
    rounded: "{rounded.compact}"
    padding: "10px 12px"
  date-option-selected:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.option}"
    padding: "11px 14px"
  metric-chip:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.pill}"
    padding: "12px 16px"
  unit-switch:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.option}"
    padding: "6px 10px"
  report-tabs:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.compact}"
    padding: "12px 18px"
  report-card:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.panel}"
    padding: "clamp(28px, 3.4vw, 48px)"
  quality-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "32px"
  disclosure:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel-small}"
    padding: "24px"
---

# Design System: SolarOps Audit landing

## Overview

**Creative North Star: "숫자부터 근거까지"**

Let a reader inspect solar-generation numbers and follow their evidence without moving the page around them. SolarOps navy and gold, bold Korean sans typography, generous full-width fields and one atmospheric landscape establish a calm, factual Persuade surface. The product fragments remain legible, editable HTML and SVG; the photograph provides setting.

This document belongs to the independent static artifact rooted at landing/. The FastAPI application and repository-root design files belong to the dashboard. The current v5 direction supersedes the earlier randomized direction and v1–v4 assessments. Leedlime informed the photographic split hero; Beacon informed broad fields, whitespace and a short evidence-led flow. Their claims and product UI were not copied.

**Key Characteristics:**

- A full-width landscape, a neutral contrast scrim and a stationary split hero.
- Pretendard headings and tabular data numerals with three prominent historical processing figures.
- One boundary per product panel; full-width section fields and whitespace carry hierarchy.
- Real saved public-data aggregates rendered as HTML text and SVG geometry.
- Direct-action feedback with reserved content height and reduced-motion support.

The normative tokens above were extracted from [styles.css](styles.css); interaction descriptions were checked against [site.js](site.js) and the current [markup](index.html). Existing [desktop](../docs/portfolio/images/landing-20261023/desktop-v5.png), [tablet](../docs/portfolio/images/landing-20261023/tablet-v5.png) and [mobile](../docs/portfolio/images/landing-20261023/mobile-v5.png) v5 captures are the primary visual evidence. Desktop and mobile fold captures were visually reviewed during documentation. This document pass did not run new browser checks; executed checks and their limits belong in [QA.md](QA.md).

## Colors

Deep blue-black grounds the evidence; warm solar gold directs attention to generation and selection, while pale neutral and sage fields give the long page breathing room.

### Primary

- **Solar Gold** (**gold**): estimated-energy figures, SVG bars, selected units and dates, source links on dark panels. It is a reading cue, not a claim of financial gain.
- **Night Navy** (**ink**): body text, primary actions, report/chart panels and the technical-evidence field.

### Secondary

- **Measured Green** (**green**): valid-slot bars, markers and quality references.
- **Invalid Ochre** (**invalid-ochre**): invalid-slot encoding; keep it distinct from missing slots and upstream interpolation.
- **Focus Blue** (**focus**): visible keyboard focus for links, buttons and summaries.

### Neutral

- **Cool Canvas / White Surface** (**canvas**, **white**): page canvas, quality/lineage panels and reversed hero actions.
- **Quiet Paper / Sage Field / Warm Closing** (**paper**, **quality-field**, **closing**): secondary reading surfaces, quality comparison and the final action field.
- **Body Slate / Inverse Slate** (**muted**, **inverse-muted**): contextual text on light and dark surfaces respectively.
- **Landscape Foundation** (**hero-foundation**): fallback behind the full-width photograph.
- **Control Slate / Menu Slate / Hover Slate** (**control-slate**, **menu-slate**, **menu-hover**): the custom date control and its dark popup.
- **Control Edge / Dark Divider** (**control-border**, **dark-divider**): input boundaries and functional table/chart rules.

### Named Rules

**The Evidence Color Rule.** Color distinguishes data roles and control states; labels retain the meaning, including valid, invalid, missing and overlapping interpolation.

## Typography

**Display Font:** Self-hosted Pretendard Variable 1.3.9, with Malgun Gothic and sans-serif fallback.
**Body Font:** Pretendard, with Segoe UI, Malgun Gothic and sans-serif fallback.
**Label/Mono Font:** Pretendard for labels; Consolas and monospace for CSV, JSON and hashes where specified.

**Character:** A single Korean sans family ties the explanatory copy to the actual product. Bold headings, compact tracking and tabular numerals establish hierarchy without editorial serif styling. The page subset uses SIL OFL; the original font is retained.

### Hierarchy

- **Display:** The frontmatter display role governs the two-phrase hero heading. At widths up to 800px it uses clamp(32px, 6.5vw, 48px); up to 600px it uses clamp(30px, 8.5vw, 44px).
- **Headline:** The headline role governs section titles; phone titles use 32px. The closing heading has its own observed range of 36–58px, falling to 32px at smaller widths.
- **Title:** The title role is the general third-level heading. Compact product-panel titles use 22px.
- **Body:** The body role is 18px on desktop and 16px at widths up to 600px. Hero lead copy uses a 1.7 line height and a 440px maximum width.
- **Label:** Metadata is generally 13–14px. Keep small source and photo credits secondary without turning them into unreadable decoration.
- **Metric:** The three historical processing figures use the metric role; at widths up to 800px they use 38px with 18px units. Desktop units are 22px. Hero energy has its own responsive 36–58px range, 30–44px on phones.
- **Code:** CSV and JSON use the code role in the dark report pane. Format saved numeric values for display without changing their source precision.

Typography research: actual computed styles on [Channel Talk](https://channel.io/kr) and [flex](https://flex.team/) used Pretendard; headings used 600/700. [Pretendard](https://github.com/orioncactus/pretendard), [SUIT](https://sun.fo/suit/) and [Wanted Sans](https://github.com/wanteddev/wanted-sans) official descriptions were compared. This is a small observed sample, not a market-share ranking. Bold Pretendard replaces the rejected Gowun Batang headings and aligns with the product. Old font assets are preserved but not loaded.

### Named Rules

**The Saved Precision Rule.** Tabular numerals aid comparison; display rounding never replaces independently retained source values.

## Layout

The content frame is at most 1280px wide, with 32px outer gutters, reducing to 20px at widths up to 600px. Full-width section colors extend beyond that frame. Desktop explanatory sections generally pair two columns, separated by 80–100px; the spacing contracts at 1100px, while 800px and 600px breakpoints reorganize content progressively.

The hero uses a 1fr / 1.06fr split, a 64px gap and a 760–920px viewport-related height. Copy and action sit left; the monthly report sits right at approximately the former photographic-tile width. At 800px the hero stacks, with a report maximum width of 620px. The landscape covers the entire field; its small gray source link sits in a corner.

The story runs hero → three large historical processing figures → monthly chart/quality → metric comparison → report formats → source lineage → technical evidence → FAQ → action. Historical figures use three columns on desktop and tablet, then three horizontal number/label rows on phones. Product overview panels use a 1.6fr / 1fr grid before stacking at 800px. Broad sections typically use 64–112px vertical spacing.

Reserve height when interactions change content: the metric explanation has a minimum of 6.6em; the report-format viewport is 340px high, changing to 390px at widths up to 800px. Table and code overflow remains inside its relevant product surface. There is no nested decorative presentation frame.

### Named Rules

**The Stationary Surface Rule.** No entry or scroll reveal, observer-driven panel movement, or parallax; only deliberate user actions trigger local feedback.

## Elevation & Depth

The system uses no box shadows. Depth comes from full-width tonal fields, the real landscape under a neutral contrast scrim, and single opaque product surfaces. The desktop scrim moves from 94% to 42% dark opacity; at widths up to 800px it becomes a uniform 72%. The date popup uses a visible slate boundary and a local stacking layer rather than a floating-card shadow.

### Named Rules

**The One Boundary Rule.** A product fragment receives one panel boundary; do not wrap it in another decorative card, browser mockup or screenshot frame.

## Shapes

Product panels use the panel and panel-small radii. Controls use compact and control radii, with small option corners inside a date list or unit switch. The rounded metric selector is an actual grouped control, not a decorative label. Functional tables and lineage rows retain dividers; large section fields remain unframed. Solid-circle valid, square invalid and dashed missing markers supplement color.

## Components

### Buttons

Confident, readable actions with a quiet surface change.

- The primary button uses navy with white text; the inverse variant uses white with navy text on the hero. Both use the control radius and 16px / 24px padding, with a minimum height of 54px.
- Header actions are compact variants with the header radius. Their mobile padding and type scale with the header.
- Hover changes background; focus uses a 3px blue outline with a 5px offset. Active presses use brightness feedback.
- Color transitions last 180ms. Only the action arrow shifts horizontally by 3px over 180ms using the extracted easing curve. Reduced motion disables transitions and the arrow shift.

### Chips

Selection controls express an explicit state.

- The metric pill group uses a pale sage track, transparent inactive buttons and navy/white selected buttons. Hover uses gold/navy. Its three states are observed, valid and interpolated.
- The compact kWh/MWh group uses a dark slate track and gold/navy selection. Values come from the saved PS_001 report value of 585,980.279 kWh and display two decimals.
- Both metric control groups synchronize the same explanation and aria-pressed state. Upstream interpolation remains overlapping information; do not add it to the valid/invalid split.

### Cards / Containers

Single opaque surfaces contain usable product content.

- Report and chart panels use navy; quality and lineage panels use white. Standard product corners are 16–20px, with no shadows.
- Report padding scales from 28px to 48px; overview panels use 32px before shrinking at smaller widths. Phone product padding is generally 24px / 20px.
- The monthly chart contains 30 saved dates as SVG bars, pointer/focus tooltips, roving keyboard focus, arrows/Home/End and previous/next controls. The accessible table retains three-decimal daily values.
- Chart bars use a 160ms fill transition in the current CSS. Result text uses a 180ms opacity-only response from 0.82 to 1 after direct actions. Neither changes panel position; reduced motion disables both.
- Source screenshots are comparison evidence, with one full-capture link in the product overview. All shown product content is HTML/SVG; the background photograph is the only displayed raster image.

### Inputs / Fields

The date field is a custom keyboard-accessible slate listbox, not an OS-native dropdown.

- The trigger and date options have a minimum height of 44px. Trigger corners are compact; the popup uses control corners and option rows use small option corners.
- The trigger shows its expanded state with a gold edge; the selected option uses gold/navy. Option focus uses a 2px pale outline inset by 2px.
- Enter or Space activates the focused native button. Escape closes and restores trigger focus; arrows, Home/End and PageUp/PageDown move option focus. Outside pointer or focus closes the popup.
- The popup opens above or below according to available viewport space. Its maximum height is constrained to the available space in the current script.
- Date options, tables and code share thin muted slate scrollbars against dark surfaces. Tables and code reserve scrollbar space. Disabled previous/next controls visibly reduce opacity.

### Navigation

The wordmark, three short section links and compact action sit over the photograph. Links use small, medium-weight type with visible keyboard focus; hover softens their color. The last section link hides at 1100px and the section navigation hides at 800px, while the wordmark and primary action remain. No sticky overlay or animated navigation panel is introduced.

### Report Formats and Lineage

HTML, CSV excerpt and JSON excerpt tabs share a fixed-height report viewport. The selected tab uses navy/white; keyboard Left/Right/Home/End changes the active tab and focus. The downloaded CSV is the original public PS_001 report output; the JSON preview declares its limited saved scope.

Lineage uses real report ID, generated timestamp, calculation/input versions and source manifest hash. Native disclosure exposes the details; clipboard copy has a selectable-text fallback. Native FAQ disclosures remain usable without JavaScript. With JavaScript disabled, factual text, chart, table and report stay visible while enhancement buttons remain disabled.

## v6 Composition

The hero centres the badge, headline, lead and two CTAs over the photograph, then places one product window: a slim chrome bar (address shows the active view, "저장된 공개 집계 · 실시간 아님"), a sidebar with three tabs and period/source/time-zone scope, and a dark main area. Panels inside the window are the only inner boundaries. Overview holds four KPIs, the interactive daily chart and quality composition; the report view holds the unit toggle, PS_001 daily bars with sub-50% valid days marked, and the daily table; lineage holds versions, IDs/hash copy and the 30-partition valid-ratio grid. On desktop all views share one height; at 800px and below the sidebar becomes a top tab row and only the active view renders. Below the hero, the report section shows a document-style HTML summary and the lineage section a four-step publication flow with the failure branch.

## Do's and Don'ts

### Do:

- **Do** preserve Pretendard sans typography, the full-width photograph as the stage for the single demo window, three large historical statistics and one boundary per product panel inside it.
- **Do** render product panels as HTML/SVG and keep source screenshots as comparison evidence.
- **Do** keep direct-action feedback local: 180ms opacity/color responses, the current 160ms chart fill, and a 3px action-arrow shift; honor reduced motion.
- **Do** retain the keyboard-accessible slate date listbox and consistent dark scrollbars for dates, tables and code.
- **Do** distinguish 51 plants, 14,400,480 inverter rows and 12,572 published day partitions from the April 2024 overview of five plants and the PS_001 monthly report.
- **Do** preserve the 0.002 kWh daily-rounding difference from the independently retained monthly total, source lineage and original report artifacts.

### Don't:

- **Don't** reintroduce Gowun Batang headings, nested presentation frames, moving panels, entry/scroll reveals or parallax.
- **Don't** substitute screenshot images for the editable product UI or add invented chart gaps or simulated live changes.
- **Don't** turn estimated energy or review candidates into measured energy, confirmed faults, financial losses or commercial-success claims.
- **Don't** imply a backend connection, customer upload, live monitoring or new publication from this independent static landing.
- **Don't** copy customer, revenue, accuracy, conversion or uptime claims from visual references.
- **Don't** overwrite dashboard-owned root design files or treat older captures as the current visual specification.

[Saved preview provenance](assets/data/preview.json) records read-only public API/report sources; matching data is embedded in the static page. Photo source and detailed data scope remain in [evidence.html](evidence.html), with [asset provenance](assets/images/README.md). Redundant preview/capture disclaimers are intentionally absent from the main composition. See [COPY.md](COPY.md) and [QA.md](QA.md) for copy and executed-check boundaries.
