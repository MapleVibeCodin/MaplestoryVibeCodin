# Step 13 — 1,000 new images, RuneScape-inspired shadow recognition

2026-11-27. Isolated lab branch. Do not deploy or merge into production on this evidence.

## Source and corpus integrity
Recovered two older FM SCAN recordings and a later 04-39-52 recording in addition to the unused Step 12 archive frames. Selected 1,000 distinct real 225x344 observation crops, with 1,000 unique inventory crop SHA-256 hashes and zero overlap with the 1,000 Step 12 inventory hashes or source indices. No synthetic images. 950 initially selected shop-interval frames and 50 controls; review of the 30 late-recording controls revealed 18 visible shops and 12 channel-dialog occlusions, making the corrected set 968 visible-shop interval frames and 32 controls. All 20 other controls were visually inspected. Repeated frames from the same stores remain; this is not 1,000 independent shops or exhaustive frame-by-frame labeling. No raw private media, logs or reference arrays pushed to GitHub.

## Method
The original shadow implementation adapts Simba/SRL/WaspLib's documented ideas: constrained search regions, color tolerance landmarks, bitmap masks, and sprite matching. Reference sources: https://srldocs.github.io/SRL/wrappers.html ; https://docs.waspscripts.com/spritepixels.html ; https://waspscripts.com/tutorials/simba-tools-by-torwent . No third-party source copied. A fixed 225x344 OBS observation crop is checked against 100 color landmarks in three button groups. Then compare the six visible rows against a *known*, separately sampled reference item name mask and sparse sprite pixels. Exclude seller, price, stats and stack count from the name mask. The second revision rejects duplicate names before sprite confirmation, rejects large blue channel header, tolerates partial cursor obstruction of one button. Production native geometry and strict scroll checks not changed.

## Executed measurements (Linux, predecoded images)
| Metric | Old Step 11 prep on same 950 initially positive frames | Step 13 v1, same 950 | Step 13 v2, corrected 968 positives |
| --- | ---: | ---: | ---: |
| P50 ms | 3.2972 | 0.3396 | 0.3514 |
| P95 ms | 4.2633 | 0.4475 | 0.4581 |
| Max ms | 6.1604 | 1.4512 | 3.2847 |
V2 all 1,000: P50 0.3504ms, P95 0.4575ms, P99 0.6122ms, max 3.2847ms; all <=50ms. Standalone replay with PNG hash validation: same decisions, P95 0.4597ms, max 2.9925ms. Roughly 9x faster than old preprocessing, but distinct scopes: old path prepares OCR input, new matches already-known visual templates without OCR. No disk decoding, Windows capture, OCR, UI polling or overlay drawing timed.

## Recognition results and error review
Nine apparent v1 wrong detections were actually target-present frames after in-shop scrolling; checked those images visually and corrected provisional interval labels. Corrected-label v1: shop gate 926/968 accepted, 24/32 controls rejected. Unique target 380/388 correct; 285/340 expected no-highlight cases rejected, 55 duplicate false highlights. V2 same-corpus retest: gate 958/968 accepted, 32/32 controls rejected. Nine known target templates. 386/388 expected unique matches, 2 misses, no wrong row in those scored unique cases; 340/340 expected reject cases, 0 observed false highlights there; 272 target cases unscored. This is same-corpus tuning, and the interval labels are not independent exhaustive ground truth. Templates are often from the same shop episode in another frame, so do not claim cross-shop generalization or unknown-item name recognition. V2 retained 10 shop-gate misses including leave-button cursor occlusion; expected unique misses: Arwen's Glass Shoe frame 430 (no match), Cherry Layered T frame 991 (gate reject). Negative examples include channel dialog overlay and ordinary room views.

## Artifacts / next steps
Shadow functions saved at performance-lab/research/step13_rs_shadow.py. Full private 1,000 PNG crop archive, per-image JSON (both versions), scripts and local derived reference masks packaged in the downloadable Step 13 benchmark kit. Standalone replay executed successfully. Repo contains original algorithm only and aggregate results, not private images. Next: held-out stores, independently labeled native captures, icon/name ambiguity and sold/selected/tooltip tests, then actual Windows capture-to-overlay timing. No 50ms end-to-end pass established; no production change or automatic input authorized.
