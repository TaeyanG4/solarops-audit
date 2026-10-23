# Product screenshot provenance

2026-10-23 Asia/Seoul, local running SolarOps Audit at `http://127.0.0.1:8502`. Actual BR-PVGen public data, April 2024. The source application was not edited for this landing task. Another workstream deployed product changes during capture, so these images are dated capture evidence rather than a claim that every image came from one release.

| Asset | Source view | Capture treatment |
|---|---|---|
| overview-full.webp | `/?view=overview&period=2024-04&source=public` | 1440×2042 full-page capture at a 1440×1100 viewport, DPR 1, lossless WebP |
| overview.webp | Same overview | Crop `(244,339)–(1420,1137)` (1176×798) from the full original; complete chart and quality panels, with about 12px of native background around their edges |
| overview-mobile.webp | Same overview | 390px viewport, DPR 2; trend-panel crop from full-page capture |
| quality.webp / quality-mobile.webp | Same overview | 390px viewport, DPR 2; quality-panel crop, identical files |
| report.webp | `/?view=reports&period=2024-04&source=public&plant=PS_001` | Desktop report-band element capture |
| report-mobile.webp | Same report | 390px viewport, DPR 2; report-band crop from full-page capture |
| lineage.webp | Same report | Desktop report-snapshot element capture |
| lineage-mobile.webp | Same report | 390px viewport, DPR 2; report-snapshot crop from full-page capture |

The first desktop crop stopped at viewport height and clipped the panel bottoms. The v2 capture replaces it with the complete pair; the rejected viewport original and first crop evidence remain in `artifacts/landing-20261023/` and the initial delivery renders.

Only rectangular crops and lossless PNG→WebP encoding were performed. No changed numbers, invented UI, compositing, recoloring, sharpening or generated artwork. The product's upstream interpolation display evolved during the other workstream; the landing uses the common rounded 9.9% and explains that interpolation is a separate attribute. Original PNGs, full-page captures, crop coordinates and rejected clipped captures remain in Git-excluded `artifacts/landing-20261023/`.

The screenshot values derive from BR-PVGen V.1 by Caian Dutra de Jesus, Rhuan Nascimento Ferreira and Eduardo Pestana de Aguiar (UFJF), [DOI 10.5281/zenodo.21511487](https://doi.org/10.5281/zenodo.21511487), CC BY 4.0. Attribution appears in the landing footer and evidence page. Screenshots are not customer data. Energy is estimated; review candidates are not confirmed failures.

## Current v5 display and comparison captures

Only the landscape is displayed as a raster in the main page. All product panels are editable HTML/SVG backed by saved public aggregate values in `../data/preview.json`. Source screenshots remain available through the full-capture link and retained files; they are not passed off as interactive images.

Additional 2026-10-23 source captures used Chromium at 1440×1100 CSS pixels, DPR2. `overview-full-2x.webp` is the complete 2880px-wide overview. `trend-2x.webp`, `quality-2x.webp`, `report-2x.webp`, `lineage-2x.webp` are full panel crops with coordinates in `artifacts/landing-20261023/capture-source-v5.json`. Source PNGs are preserved beside that file. All are lossless; no sharpening, invented UI or number edits. Old assets and v1–v4 renders are retained as history.

The intermediate `overview-trend.webp` crop is `(12,12)–(714,786)` and `overview-quality.webp` is `(738,12)–(1164,786)` within the old overview.webp. They are retained but no longer rendered by the page.

## Landscape

`solar-landscape.webp`: GlacierNPS, [Solar Panels at Logan Pass](https://commons.wikimedia.org/wiki/File:Solar_Panels_at_Logan_Pass_(51420891744).jpg), [original Flickr photograph](https://www.flickr.com/photos/glaciernps/51420891744). Wikimedia Commons identifies it as public domain. Source metadata and 1920×1280 JPG are preserved in `artifacts/landing-20261023/solar-landscape-provenance.json` and `solar-landscape-source.jpg`. Converted to WebP at quality88 (361,172 bytes). CSS crops the photo and places a neutral scrim for contrast. It depicts the product’s subject context, not a SolarOps customer or analyzed BR-PVGen facility. The small hero credit links to `evidence.html#visual-sources`.

## Fonts

Pretendard Variable 1.3.9 is from the existing product, with its [OFL license](../fonts/OFL.txt). `PretendardLanding.woff2` is a fontTools subset for the current HTML/JS text plus ASCII, preserving variable weights/OpenType layout. The unchanged full `PretendardVariable.woff2` remains available. Rebuild the subset when copy adds glyphs. Gowun Batang from the v3 experiment and its license are preserved, but neither is requested or used by the current page.

The favicon is copied from the existing product. Fonts and photograph are self-hosted; no remote font requests or video.
