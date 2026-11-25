# FM Rush — public color-vision source audit, 2026-11-26

## Purpose and constraints

Improve the passive FM Rush recognition overlay using proven visual-recognition techniques from RuneScape color-vision frameworks and MapleStory Classic-specific projects. Preserve all previous source, tests, media references, branches and configurations. Keep existing UI, manual clicking, chase/ARMED behavior, hotkeys, browser v24.56.0, camera profiles and archives unless explicitly changed. No automated gameplay inputs, memory reading, client modification or bypass mechanisms. Do not suggest Work or Codex. Research source code directly, distinguish measured results from claims, and prioritize systematic replay over item-specific exceptions. Do not import entire bot frameworks.

Baseline v24.63.0 runtime c27c8671630225d94133e4194d5ac4584e5e0b8c; prior continuation c862d15d562a3222a696a3363fc64ca710116b9e. Published safeguard release v24.63.1: 68b8b7a1cbe75d805ab78314458f8ff1c72a1ed5. This document is research, not a release of the proposed new engine.

## Primary source inventory

Pinned links use exact tree/commit identifiers retrieved during source audit; branch links are mutable. The audit retrieved recursive trees for eight principal repositories and read selected source files. The following links are for study, not a claim that all external tests were executed. Check each repository's LICENSE and third-party assets before copying or distributing. Minerva and mpl-ocr were reported MIT; Simba, WaspLib, SRL-Development and ChromaScape were reported GPL-3.0. Do not assume SimpleOCR, OS Bot COLOR, SRL-T or legacy SRL has a permissive license. Keep attribution and comply with applicable terms. Do not redistribute third-party source or assets merely because they are public.

### Minerva — highest priority: same-game shop reader and real regression

Repository: https://github.com/itechify/minerva
Inspected tree: 5d90302b44715cb303b0a2b601c5bab4cb0fb4e4
- https://raw.githubusercontent.com/itechify/minerva/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/crates/minerva-core/src/player_shop.rs (931 lines, blob ae384f04cf41a0dab16d45c20de750122517fb3b): find_lists, listings, line_extent, clean, covered, picture_tier; repeated inventory bands, brightness, UI sizing, text extraction, selected/sold rows, tooltip and scroll-tier evidence.
- https://raw.githubusercontent.com/itechify/minerva/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/crates/minerva-core/src/deal_finder.rs (504 lines, blob 60eecad5853924737c2a56eaeba71628e4a62818): same_slot, whole, item_named, tooltip_named, picture_named, cut_start; uncertain names/price do not receive another item's verdict; covered results explicitly distinguished.
- https://raw.githubusercontent.com/itechify/minerva/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/crates/minerva-core/tests/player_shop_samples.rs (588 lines): public pipeline inputs, actual PNGs and JSON labels, changed UI size, occlusions, sold transitions, background false positives, truncated item disambiguation.
- https://raw.githubusercontent.com/itechify/minerva/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/crates/minerva-core/tests/deal_finder.rs (960 lines): behavior, stale badge clearing, ambiguity, scaling, state transitions.
- https://github.com/itechify/minerva/tree/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/samples/player-shop : tree contains 24 PNG paths, some alternate-position variants; not necessarily 24 independent shops or independent held-out cases.
- https://github.com/itechify/minerva/blob/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/docs/adr/0014-deal-finder-finds-the-player-shop-in-the-client-area.md
- https://github.com/itechify/minerva/blob/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/docs/adr/0009-bug-reports-replay-the-cores-inputs.md
- https://github.com/itechify/minerva/blob/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/docs/adr/0020-readers-find-the-ui-size-and-read-at-the-samples-size.md
- https://github.com/itechify/minerva/blob/5d90302b44715cb303b0a2b601c5bab4cb0fb4e4/AGENTS.md
- https://owlofminerva.app/

Design: find repeated light blue-gray bands sharing width and horizontal endpoint, brightness-adjusted instead of requiring exact button colors. Reference band RGB (202,213,223), width 253 px in their sample coordinate system, accepted width range 140–480, selected RGB (251,167,46); these are NOT calibrated FM Rush values. Normalize to native UI scale. Clean text pixels lie near the background-to-ink color line; unrelated colors indicate occlusion. Verify price syntax and measured ink width (their constants PRICE_W, PRICE_DIGIT_W, PRICE_COMMA_W) to detect dropped digits. Handle slot-grid changes, newly covered rows, sold-out rows, and hover tooltip naming. Their acceptance is correct or unknown; this is not equivalent to 100% recall. Do not loosen our seller identity or strict scroll policy; sprite tier alone does not identify an exact scroll. Current FM Rush target is a specific external listing, not generic per-item market evaluation.

### mpl-ocr — highest priority: same-game glyph and native-scale engine

Repository: https://github.com/Shonitbar/mpl-ocr
Inspected tree: 954487e3f2bbae7e9591e03f29f7408f7faa1391
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/docs/design.md
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/crates/mapleocr-recog/src/glyph.rs (1006 lines, blob 12796ad09bf91c1edd37d87afe31798272de3ee2): binarize_banded, pack, iou_shifted_packed, Atlas::learn, read_scored, classify, split; packed bit operations, shifted IoU, variants and baseline.
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/crates/mapleocr-imgproc/src/native.rs : area-resample to native grid, best_phase, to_native_phase; UI subpixel phase recovery.
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/crates/mapleocr-core/src/pipeline.rs : shared offline/live pipeline, pixel hash, ROI font learning, cache and semantic parse.
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/tools/mapleocr_tools/gdi.py : Windows GDI font rasterization.
- https://raw.githubusercontent.com/Shonitbar/mpl-ocr/954487e3f2bbae7e9591e03f29f7408f7faa1391/tools/mapleocr_tools/identify_font.py : render candidate fonts and compare normalized cross correlation; identify scale and smoothing.
- https://github.com/Shonitbar/mpl-ocr/tree/main/tools/tests
- https://github.com/Shonitbar/mpl-ocr/tree/main/crates/mapleocr-capture/src : capture.rs, wgc.rs, dxgi.rs, d3d.rs.
- https://github.com/Shonitbar/mpl-ocr/blob/main/crates/mapleocr-core/src/detect.rs

Reported findings: tooltip/dialogue Arial 12 px; NPC name Arial 11 px; quest helper Arial 11 px regular/bold; chat likely Arial 14 px; status numbers sprites; minimap title unresolved. Shop font not yet identified for FM Rush. GDI monochrome font rasterization can differ from Pillow/FreeType at small sizes. Use native screenshots to identify exact shop font, scale, foreground/background, baseline and spacing. GDI tools are Windows-specific. Reported fresh map OCR median 2.9 ms, cached publish 0.4 ms, acquisition-to-fresh-result ~3.6–4.4 ms, eight-region capture median 0.46 ms on Ryzen 5 3600/RTX 3060 Ti; these are upstream developer benchmarks, not replicated FM Rush results and not necessarily including settling delay. Use WinRT as fallback until comparison is measured.

### Simba 2.0 — reusable recognition algorithms

Repository https://github.com/Villavu/Simba ; inspected simba2000 tree 2591bfe12142b71d370d08f89bf08c5edc95aeaf.
- https://raw.githubusercontent.com/Villavu/Simba/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source/simba.pixelocr.pas (708 lines): TextToTPA, Locate, _RecognizeX, CompareUsingBackground/Shadow, GlyphSimilarity.
- https://raw.githubusercontent.com/Villavu/Simba/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source/simba.finder_dtm.pas (406 lines): GetSearchPoints, FindDTMOnBuffer, per-landmark tolerances and areas.
- https://raw.githubusercontent.com/Villavu/Simba/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source/simba.colormath_distance.pas : RGB, HSV, HSL, XYZ, LAB, LCH, DeltaE and channel weighting.
- https://raw.githubusercontent.com/Villavu/Simba/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source/simba.finder_color.pas : color search/count, edges, brightness.
- https://raw.githubusercontent.com/Villavu/Simba/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source/simba.matchtemplate_core.pas : cached image sums, FFT spectra and masked correlation.
- https://github.com/Villavu/Simba/tree/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Source : finder_image, matchtemplate_ccorr, matchtemplate_ccoeff, matchtemplate_sqdiff, wgcapture, colormath_aca; ide/simba.ide_dtmeditor.pas and ide/simba.ide_colorpicker.pas.
- https://github.com/Villavu/Simba/tree/2591bfe12142b71d370d08f89bf08c5edc95aeaf/Tests
- https://villavu.github.io/Simba/ ; https://villavu.com/

DTM = deformable template model: verify multiple independent spatially related color landmarks with local displacement allowance. Keep negative evidence and require unique alignment; do not just enlarge RGB tolerances. Simba pixel OCR descends from SimpleOCR and assumes fixed non-antialiased glyphs. Compare both ink and expected background. FFT correlation may be unnecessary for small fixed regions; benchmark direct packed masks first. Do not copy GPL source into the project without complying with the license.

### Other inspected code

- https://github.com/ollydev/SimpleOCR ; https://raw.githubusercontent.com/ollydev/SimpleOCR/master/simpleocr.engine.pas (717 lines, blob 66bae1eab45308e62b477ec46db27e11aa2e9118); https://raw.githubusercontent.com/ollydev/SimpleOCR/master/simpleocr.filters.pas (248 lines). TextToMatrix, TextToTPA, LocateText, RecognizeStatic; target text foreground/background, color/threshold/shadow filters. Expected text can be precompiled from HeneFM before shop opens. Do not treat visually matching prefix as verified full string.
- https://github.com/dustyfence/OS-Bot-COLOR tree fa009ca1b34811209f5713bcdc8b7c21126f2ca9 ; https://raw.githubusercontent.com/dustyfence/OS-Bot-COLOR/main/src/utilities/ocr.py (238 lines), https://raw.githubusercontent.com/dustyfence/OS-Bot-COLOR/main/src/utilities/color.py ; find_text, extract_text, per-character template matching, sorting positions. Archived project; ~2 ms text-location claim is upstream, not replicated.
- https://github.com/WaspScripts/WaspLib tree 0d741b2f208a9f67ead488674df6cd48f7e1afce ; https://raw.githubusercontent.com/WaspScripts/WaspLib/main/utils/ocr.simba (370 lines, SameGlyph, SameText, NormalizeGlyphs, RecognizeStatic); https://raw.githubusercontent.com/WaspScripts/WaspLib/main/main/finders/itemfinder.simba (501 lines, alignment, mask, cleanup, hash candidate lookup); https://raw.githubusercontent.com/WaspScripts/WaspLib/main/main/interfaces/mainscreen/finders/colorfinder.simba (474 lines); https://docs.waspscripts.com/ocr.html ; https://github.com/orgs/WaspScripts/repositories. Treat identical glyphs as ambiguous, not automatically normalize to the expected listing.
- https://github.com/Villavu/SRL-Development tree f1319a3e7e77fe8739d4682b69de127a821f2242 ; https://raw.githubusercontent.com/Villavu/SRL-Development/master/utils/color.simba (CTS0/1/2, channel weights, bounded searches); https://raw.githubusercontent.com/Villavu/SRL-Development/master/osr/ocr.simba ; https://srldocs.github.io/SRL/color.html
- https://github.com/StaticSweep/ChromaScape tree 5ea3b995f5d13e19c592a6399973fe7dadb5e656 ; https://raw.githubusercontent.com/StaticSweep/ChromaScape/main/src/main/java/com/chromascape/utils/core/screen/topology/ColourContours.java (201 lines, HSV ranges, morphology, contours); https://raw.githubusercontent.com/StaticSweep/ChromaScape/main/src/main/java/com/chromascape/utils/core/screen/topology/TemplateMatching.java (291 lines, alpha masked TM_SQDIFF_NORMED); https://raw.githubusercontent.com/StaticSweep/ChromaScape/main/src/main/java/com/chromascape/utils/domain/ocr/Ocr.java (366 lines, font cache, duplicate suppression).
- https://github.com/Torwent/SRL-T tree 8adff16130e51b3a4d51f5cc1baf2c10a3e09d8e ; https://raw.githubusercontent.com/Torwent/SRL-T/master/main/finders/itemfinder/itemfinder.simba (624 lines); https://raw.githubusercontent.com/Torwent/SRL-T/master/main/finders/itemfinder/hash-generator.simba ; https://raw.githubusercontent.com/Torwent/SRL-T/master/main/ocr/ocr.simba. Sprite fingerprints narrow candidates; exact pixel/identity verification still required.
- Additional research leads (not fully audited): https://github.com/SRL/SRL ; https://github.com/SRL/SRL-6 ; https://github.com/Torwent/WaspLib ; https://waspscripts.dev/ ; https://www.slyautomation.com/ ; https://github.com/slyautomation/osrs_basic_botting_functions ; https://github.com/jacobbrown0192/OSRS-Computer-Vision-Bot
- Generic capture and vision references: https://github.com/ra1nty/DXcam ; https://docs.opencv.org/4.x/de/da9/tutorial_template_matching.html ; https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/desktop-dup-api ; https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-getglyphoutlinew ; https://github.com/RaiMan/SikuliX1

## Proposed passive recognition architecture

1. Capture timestamped client pixels. GDI cropped capture baseline; benchmark WGC and DXGI against actual visible-change-to-highlight latency, not FPS alone. Shared consistent frame prevents mixing states; retain focus/geometry checks and stale-frame invalidation.
2. Keep confirmed FM-room gate; detect shop with current exact three-button fast path plus shadow-mode repeated band geometry, brightness/scale, negative-space and multiple landmarks. Compare confidence on unrelated UI and all-sold/empty shops; never allow a tolerant single pixel signature to trigger a match. Do not enable experimental replacement yet.
3. Detect active, selected, sold, empty and covered rows using geometry and foreground/background blend. Compare normalized/prepared pixel hashes to avoid repeated recognition while retaining raw evidence for stale invalidation.
4. Identify actual native font with labeled native screenshots. Generate GDI glyph atlas locally, recover scale/subpixel phase. Packed XOR/popcount, shifted IoU, spacing/baseline, segmentation or dynamic programming. Precompile target seller/name/price masks from expected feed, but include hard negatives/competing strings (scrolls, percentages, lesser variants, similar sellers, digit confusion). Never assume visually identical glyphs are resolved by expected listing. Use WinRT fallback and reject disagreement.
5. Candidate sprites/alpha masks, color clusters or hashes only narrow candidates; cannot prove item/stats by themselves. Full seller, full item, numeric price, current row identity, unique visible evidence required. Truncated/occluded rows unknown unless independently verified by a full tooltip under correct row. Non-scroll rounding only amber; strict scrolls never accept rounded/partial names. Physical price ink width independently checks dropped/extra digits; grouped/ungrouped price grammar now stricter in v24.63.1. Quantity vs unit price needs explicit semantics before changing.
6. Revalidate same target generation, seller, row pixels, shop and room before publish; fresh evidence lifetime; clear on capture failure, scene/focus/geometry change, close, stale target; if partial evidence changes, only single unchanged non-scroll amber/orange candidate, strict scroll recheck.
7. Offline inspector and replay: expose ROI bounds, pixel masks, glyph candidates, score margins, negative evidence, occlusion, stage outcomes and timings. No raw OCR/names/images added to ordinary performance telemetry; preserve privacy. Replay same core as live, not a separate approximation. No automated inputs.

Suggested modular design (not yet created except vision_guard.py): vision_capture, vision_color, vision_geometry, vision_font, vision_text, vision_digits, vision_sprite, vision_shop, vision_cache, vision_replay, vision_benchmark, vision_inspector. Keep existing FM Rush interface rather than wholesale rewrite. Event-driven state machine: confirmed room -> shop appeared -> seller verified -> inventory changed -> item/price uniquely verified -> publish; invalidation transitions are first-class.

Provisional engineering goals only: room 1 ms, shop 2 ms, seller 2 ms, six rows 5 ms, price 3 ms, final validation 2 ms; 15 ms recognition processing excluding acquisition/queue/render, under 50 ms end-to-end fast path aspirational. Measure p50/p95/p99, failures, missed/false positives and time to clear stale results. No guarantee.

## Known hardships and mitigation matrix

- Brightness/compression/anti-aliasing: calibrated per-mode color/shape tolerance and scale; distinguish video from native capture, avoid relaxing thresholds to chase one bad frame.
- Same-color objects: multi-landmark geometry, expected repeated bands, negative samples, uniqueness.
- UI scale/DPI/moved windows: invalidate geometry, native normalization, remeasure rather than stack offsets.
- Glyph collisions O/0, I/l/1, truncated text, touching glyphs: reject ambiguity, foreground and background evidence, competitor margin and independent tooltip; never guess missing text.
- OCR silently drops digits: strict ASCII price grammar, independent digit masks and physical text-width verification (latter pending).
- Cursor/tooltips, selected orange and sold rows: per-row occlusion/contrast; retain only explicitly non-current candidate if current evidence supports; no highlight for unverified scroll.
- Black, missing, repeated or malformed frames, capture error, focus/scene/geometry loss: clear stale hits; bound lifetime and record capture age; same pixels alone cannot prove freshness if capture backend returns stale frames.
- OCR timeout/worker crash: existing 8 s worker timeout/restart, exception guard and bounded backoff; no old match during failure.
- Changes during recognition: generation guard, final capture and exact row evidence; no green retention across changed evidence.
- Hidden/changed competing rows: reject uniqueness certainty; regression with duplicate targets and target disappearances.
- Regression escapes: stage tests before installation; fail closed if environment unavailable; shared core, independent labels, hold out complete sessions; do not claim accuracy based on repeated correlated video frames.

## Existing release and remaining safeguards

v24.63.1 68b8b7a1cbe75d805ab78314458f8ff1c72a1ed5: original vision_guard.py strict price parser, 350 ms maximum highlight age, changed-evidence guard; shop_inventory.py clears old hits on missing capture, renews exact unchanged fresh crop, catches exceptions and backs off; updater stages guard plus tests and refuses replacement if Python absent. Browser v24.56.0 untouched. Existing exact shop gate intentionally kept. See Scanner Nov 20/transcripts/2026-11-26-color-vision-failsafes.md. Prior response reported five standalone safety test groups and ten static source checks passing; four tracker integration checks staged; no independently rerun Windows tests or video replay for v24.63.1 in this documentation checkpoint. Freshness bound is provisional and may need measured tuning.

Pending: inventory-band detector shadow-mode, font identification, glyph engine, price-width cross-check, separate release telemetry (record both ARMED and LOCKED and all terminal outcomes), shared capture benchmark, source license verification, all-video and historical image full-pipeline replay. No experimental features have been deployed by this documentation update.

## Acceptance and rollout

Zero wrong green highlights, wrong seller/scroll/price acceptance, stale highlights. Target 100% correct recognition of clearly visible labeled targets, separate recall and false-positive rates, classify unreadable/ambiguous separately (not a pass). Same codepath offline and live. Include actual 10 videos/42 recent PNGs/116 unique historical image references, plus independently labeled external fixtures where compatible and licensed. Group train/calibration/held-out by whole recording or session, never nearby frames split across groups. Report confidence limits and never imply universal 100% accuracy from a finite corpus.

Implement in increments: preserve baseline -> benchmark upstream methods -> native font identification -> glyph/price verification -> robust geometry -> labeled replay -> shadow-mode old/new comparison -> Windows staged tests -> promote only after actual improvement. No further item-specific patches without evidence. All historical files retained.
