# R3 all historical FM video replay — 2026-11-27

User requested both engines be run over every previous FM recording, not just the previous 1,000-image samples. No production runtime changes.

## Corpus
27 accessible FM-related MP4 files decoded (16,455 frames, 320.4167 seconds). 25 original recordings plus two lower-resolution re-encodings of FM SCAN 2/3; duplicate upload entries excluded by filename/archive provenance, selected files hashed. The October 15 MapleStory project MP4 could not be materialized: no authorized raw-byte path. Exclude unrelated personal videos. Ten Nov26 recordings recovered from complete checkpoint ZIP; remainder from Library. Full decode passed the observed frames, not a claim about container-advertised count. All 27 file-level SHA256 hashes and per-video counts retained in private replay report.

## Executed methodology and limits
Used the actual pinned R3 RuneCache/VisualBank/visual_key from the verified R3 ZIP (SHA256 ab1dfe18d08d74b081ec46cdedc142efc6c86754994a464dc3b645669f732082), alongside an equivalent manually transcribed pinned Step11 NameOCRCache, selected/sold masks, name fingerprint and NumPy PNG preprocessing. Persistent separate Linux Tesseract instances, not Windows WinRT. Identical frame sequence, no preloaded templates, chronological independent caches, alternated engine execution order in dense run. Original Step13 OBS tolerant three-group shop gate (shadow, not native runtime), corrected inventory crop (428,284,204x263) verified on readable archived rows. Full fixed gate on all decoded frames, menu/black sample at 2Hz only. Dense recognition run evaluated every one of 2,039 fixed-gate positives across nine recordings; seven had no eligible unobstructed, unsold row. 2,032 scans per engine, 8,407 row comparisons. OCR text accuracy not independently exhaustively labeled; no full lifecycle, live capture, actual channel ID, overlay timing, strict scroll/price path, purchase, movement speed or input-registration claim. The earlier 29 offline tests not rerun because runtime unchanged.

## Dense fixed-gate results
| Metric | MapleStory | RuneScape |
|---|---:|---:|
| Median ms | 8.2710 | 0.7740 |
| P95 ms | 38.2274 | 32.5599 |
| Max ms | 69.6685 | 80.3037 |
| Total recognition ms | 22637.401 | 14013.829 |
| <=50ms scans | 2010/2032 | 2012/2032 |
| OCR calls | 1168 | 704 |
| Cache hits | 5895 | 7049 |
| Uncached rows | 2512 | 1358 |
| Blank row results | 81 | 51 |

RuneScape ~10.7x median, ~1.62x cumulative throughput, 39.7% fewer OCR calls. Tail gain only ~1.17x. Fully cached scans: Maple median .075ms vs Rune .649ms, because bitmap/sprite extraction adds overhead. OCR-required median 15.209 vs 13.978ms. First detected frame in each of nine videos required OCR in both; Maple faster in six, Rune in three, mean 40.636 vs 41.349ms. First-gate frames are not independently verified actual shop opening time. 784/8407 exact text outputs differed (9.33%); this is not a wrong-row or accuracy count. Visual review of common differences confirmed both engines can retain OCR spelling errors, e.g. Rune cached Blue loon Shoes for Blue Moon Shoes, Maple read Skull Shitt while Rune returned Skull Shirt; Black Skull Hooded Vest persisted with a Rune error. Do not interpret speed as correctness or claim automatic first-purchase advantage. Key decision: preserve Maple baseline for cold first detection, investigate safe independently confirmed learning for Rune, do not enable speculative purchase.

## Per clip dense results
| Video (Nov 26 unless specified) | Gate frames | Maple P95 ms | Rune P95 ms | Different text/compared rows |
|---|---:|---:|---:|---:|
| 03-38-05 | 279 | 18.0173 | 11.9528 |112/1024|
| 03-42-22 | 69 |30.1936|12.3599|49/185|
| 03-46-13 |177|42.7637|35.7981|27/843|
| 03-55-12 |295|44.5251|42.4542|127/1455|
| 03-56-42 |330|37.5999|32.6061|67/1561|
| 03-58-13 |235|47.4077|32.2671|0/1109|
| 04-39-52 |351|26.1756|19.7581|190/905|
| FM SCAN 2 original |191|39.1761|34.3634|153/801|
| FM SCAN 3 original |112|35.9796|35.0361|59/524|

A separate three-Hz multiscale grayscale shop-button probe on the 18 zero-gate files located real shifted shop geometry in Oct13 and compression-altered shop geometry in the two lower-resolution FM SCAN copies. No other file had a score >=.85. This is diagnostic, not exhaustive independent negative labels. Supplemental normalized geometry results will be documented separately, not pooled into original dense run.

## Supplemental geometry-normalized full-frame replay
The broad probe confirmed three extra clips. Corrected offset for Oct13 inventory crop (986,550,204x263); native-size rendered row grid visually verified. The compressed copies were resized to 1920x1080 for diagnostic only. Replayed all frames of these three files with local shop-button template correlation >=.85; reset both caches per clip; separate from nine-video chronological run. First Oct13 supplemental run missed due to template resize rounding; fixed to original fx=.5, fy=.5, then reran Oct13 only. Keep failed initial report and corrected older_report.json, do not count failed attempt as another recording.

| Clip | Gate frames | Eligible scans | Rows | Different text | Maple median/P95 ms | Rune median/P95 ms |
|---|---:|---:|---:|---:|---:|---:|
| Oct13 07-37-58 | 960 | 933 | 4050 | 231 | 11.3224 / 42.0155 | 2.3347 / 38.3890 |
| FM SCAN 2 compressed | 187 | 184 | 767 | 120 | 9.1358 / 40.4593 | 5.4603 / 38.9080 |
| FM SCAN 3 compressed | 112 | 112 | 524 | 81 | 10.7241 / 37.1022 | .8239 / 37.2246 |

All 27 accessible video files now decoded and assessed; 12 files contained positive shop gates after normalization, 15 had no positive fixed gate or >=.85 sampled multiscale match. Across primary and supplemental protocols: 3298 accepted shop frames, 37 entirely blocked/sold, 3261 eligible recognition scans per engine, 13748 row comparisons, 1216 differing exact strings (8.84%). Aggregated workload totals only (not a common percentiles estimate): Maple 40809.832ms, 2089 OCR calls, 8583 cache hits, 3215/3261 scans <=50ms; Rune 26340.189ms, 1394 calls, 10631 hits, 3221/3261 <=50ms. Primary benchmark remains the separately reported nine-file dense comparison. Compression and different geometry are not production validation.

## Deliverables
Private downloadable `FM_Sprint_R3_All_Video_Replay.zip`, 382484 bytes, SHA256 `7cbd5ede7b6070da085b790a532ef9a355f1ca976b3472a4680ac169718dc61d`. ZIP integrity verified (16 members): all-video summary, frame-level and aggregate JSON reports, executed Python scripts, private calibration crop and visual disagreement review. No raw recordings in ZIP, no private image or raw OCR logs pushed to GitHub. Replay scripts use original container paths; instructions in SUMMARY.md. This is an offline component experiment, not a full live lifecycle qualification. No code changes or new Windows test claims.
