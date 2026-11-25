# Cross-game recognition audit and executed experiments — 2026-11-26

Five new upstream repositories pinned in manifest.json; cross-game-source.json contains eight selected files, including original licenses from ABI Market Data (MIT) and WFInfo (Apache-2.0). Pixel-OCR, RatScanner (modified Elastic license), and LostArk Market Watcher are reference-only. Archive now has 39 original text files, 13 pinned repositories. No production runtime edits.

## Source-level findings
- Pixel-OCR: font conversion, exact pixel templates, C# matching. Generate native font candidates, validate against independently labelled game screenshots. License unverified.
- RatScanner: separate icon/name recognition result types. Shared sprite ambiguity means icon alone is not identity. Modified Elastic License; references only.
- LostArk: modules/scan.py uses anchor-relative cells and a thread pool for ten rows. License unverified. Adapt bounded latest-frame scheduling for live overlay, not old-frame queue.
- ABI Market Data: collector/utils.py combines 64-bit aHash, 64-bit dHash and 24-bit HSV mean signature. Candidate evidence only.
- WFInfo: Ocr.cs and TesseractService.cs support persistent OCR instances, a numbers-only engine, color-theme detection and adaptive image scaling. Apache-2.0. No full upstream app was run.

## Experiment 1: ABI thumbnail hash
Executed isolated Python transcription of compute_thumbnail_hash in local Linux container (OpenCV 4.13.0, NumPy 2.3.5). Synthetic 35x35 BGR icon, 210 gray background, colored rectangular shape and gray center. Hash distance from base:
- Identical: 0 bits.
- Outer border changed: 0 bits.
- Single interior pixel changed: 0 bits.
- Recolored shape: 4 bits (grayscale hash unchanged).
- Equal-luminance recolor: 10 bits (grayscale hash unchanged).
1000 invocations: median 0.095774ms, p95 0.1403835ms, excluding capture. Synthetic examples, not real scroll sprites. Hash collisions observed; no proof of identity. Do not substitute approximate hashes for raw pixel revalidation.

## Experiment 2: exhaustive digit corruption
Executed JS comparison using original MIT atlas blob 5e049f7585dfe1aac171fbd66b158d62f6ac9c08. All same-shape digit templates compared by Hamming distance; ties rejected. For each template, flip each combination of 0, 1, 2, or 3 distinct pixels over its entire 14px-high bitmap. Includes whitespace/background pixels. Results:
| Flips | Cases | Exact correct/reject/wrong | Unique nearest correct/reject/wrong | Bounded <=1 correct/reject/wrong |
|---:|---:|---|---|---|
|0|10|10/0/0|10/0/0|10/0/0|
|1|672|0/672/0|672/0/0|672/0/0|
|2|22596|0/22596/0|22596/0/0|0/22596/0|
|3|504140|0/504140/0|504060/0/80|0/504140/0|
Total 527418 test cases. Bounded accepts 682, rejects 526736, zero wrong accepted in this synthetic corpus. This does not validate live capture, segmentation, different widths, shifted glyphs, occlusion, or OCR fallback. No guarantee for 4+ flipped pixels. Do not enable approximate numeric recognition as authoritative until held-out screenshot validation.

## Rollout
Continue native glyph reader in shadow mode. Exact raw seller and row evidence, strict scroll policy and generation freshness remain mandatory. Need independent native screenshot labels, whole-pipeline replay and Windows test. Production remains v24.63.4, browser v24.56.0. No gameplay automation, no full third-party application execution.
