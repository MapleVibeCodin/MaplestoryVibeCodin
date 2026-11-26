# RuneScape color vision source audit — 2026-11-26

Fresh repository searches using color/colour, computer vision, Simba, pixel and automation terms; public GitHub API metadata checked. Ranking by stars among discovered explicitly licensed, relevant repositories, including engines and frameworks, not a global exhaustive ranking or speed test. OS-Bot-COLOR (287 stars) and slyautomation/osrs_basic_botting_functions (245) excluded from copying: no explicit license verified in current trees. OSBC imagesearch.py inspected: alpha-mask normalized squared difference and optional pre-captured matrix. No claim those unlicensed repos are open source. Other candidates included SRL/SRL (24), learncodebygaming/woodcutter (23), thinkRand mining script (20). LLARS ships RS3 scripts and supports OSRS framework development; not a ready-made OSRS bot. Simba is a general engine, WaspLib extends SRL; related projects are not independent engines.

| Project | Stars | License | Pinned commit |
|---|---:|---|---|
| Villavu/Simba | 279 | GPL-3.0 | 2591bfe12142b71d370d08f89bf08c5edc95aeaf |
| StaticSweep/ChromaScape | 63 | GPL-3.0 | 5ea3b995f5d13e19c592a6399973fe7dadb5e656 |
| Gubna-Tech/RuneScape (LLARS) | 44 | MIT | 2aeca7025ed3ff7b8520732d4db293d9026746ff |
| Torwent/WaspLib | 43 | GPL-3.0 | 54a4a6b494c46e1dea2e34b54d65ad3e10c61a0d |
| Villavu/SRL-Development | 35 | GPL-3.0 | f1319a3e7e77fe8739d4682b69de127a821f2242 |

## Code-level observations
- Simba finder_color: bounded target capture, distance tolerances/channel multipliers, cached distance, sliced parallel work and early termination for counts. finder_image: transparent pixels ignored, template colors preconverted and bounded image search. pixelocr: native glyph foreground/background/shadow points, glyph similarity and text localization.
- ChromaScape ColourContours: HSV inRange, morphological closing and contours. TemplateMatching: alpha-masked TM_SQDIFF_NORMED, minimum error and threshold rejection. Ocr: font cache, per-glyph TM_CCOEFF_NORMED correlation, 0.99 threshold, suppress repeated correlation peaks.
- LLARS Color and MultiColor templates: per-coordinate color mapping, grouped coordinates, LastMatch transition state, rearm on leaving configured colors. Useful for screenshot triggers, not item identification.
- WaspLib utils/color: named colors, tolerance modes, hue/saturation modifiers and restoration of previous settings. utils/pixelshift: color-specific before/after comparisons and animation detection. ItemFinder extension delegates core recognition to SRL and adds names/IDs and tab-level helpers.
- SRL-Development itemfinder: name-to-ID mapping, cached item images, shadow removal, border checks, alignment, quantity text and sparkle masking, normalized correlation. utils/pixelshift: bounded changed-pixel counts and early acceptance length. utils/color wraps tolerance settings; osr/ocr loads SimpleOCR, not an implementation of it.

## MetaScanner applicability
Prioritize a reusable captured frame, fixed row crops, exact native glyph templates, icon candidate filtering with text confirmation, and explicit stale/ambiguous states. Keep capture transition logic independent of OCR. Validate on labeled screenshots including sold/selected rows and shared icons. No timings inferred from upstream stars or source alone. No automation integration or execution, no anti-detection research. This is a selected-source archive (15 code files and 5 original licenses), not full runnable copies. Upstream paths and blob IDs in per-project manifests; GPL source remains separately labeled with original license and not incorporated into runtime.
