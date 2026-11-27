# Step 12 — 1,000 real archived shop frames: offline preprocessing audit

Date: 2026-11-27. Isolated branch `performance-lab/step-11-50ms-target`; **not a release or production install**.

## Source integrity

Recovered the user's private `FM_Rush_2026-11-26_complete_checkpoint.zip` from the ChatGPT Library (109,961,754 bytes): 42 PNG screenshots, 10 MP4 recordings, five JSONL logs and one manifest. The videos decode to 5,777 frames in the local run. A conservative, fixed-position two-color shop-button probe found **1,382 shop-preview frame candidates** across six recordings. We selected 1,000 actual decoded frames, evenly across those candidates; **982 unique SHA-256 frame-crop hashes**. No screenshots, private videos, logs or personal data were uploaded to GitHub.

**These are 1,000 frames, not 1,000 independent shops.** Many consecutive frames show the same store. The OBS recording is compressed and scaled, not a native Windows game capture. Public FM sites such as Cozy Market and MetaCW expose large numbers of listings, but not a public corpus of 1,000 original shop-window screenshots. Cozy states that scanner images stay on the local computer; its board stores text/listing data.

## Executed offline timing

Platform: the assistant's Linux container, Python + NumPy/OpenCV; not the user's Windows PC.

Scope: per-frame Step 11-equivalent NumPy/Python image preparation: tooltip-blocked-row scan, prefix checks, seller/row pixel fingerprints, name-row hashes, six-band 3x monochrome PNG preparation and encoding. The archive was decoded before timing. The code measured **no OCR, target correctness, capture, UI polling or overlay drawing**.

| Measure | Result |
| --- | ---: |
| Shop-preview candidate frames | 1,382 |
| Actual selected frames | 1,000 |
| Unique selected crop hashes | 982 |
| Preprocessing P50 | 3.403 ms |
| Preprocessing P95 | 4.822 ms |
| Preprocessing P99 | 6.725 ms |
| Preprocessing maximum | 9.798 ms |
| Preprocessing samples at/below 50 ms | 1,000 / 1,000 |
| Unique name-band hashes | 1,593 |

The preprocessing subcomponent is comfortably below 50 ms on this platform, but **this does not establish that the scanner identifies or highlights items within 50 ms**. A valid full-system pass needs actual Windows screen capture, WinRT OCR on cold names, target accuracy labels, and visible overlay timestamps, with P95 `shop_open_to_overlay_ms <= 50` and `queue_to_overlay_ms <= 40`.

## Source inspection and fixes

The Step 11 branch had literal doubled backslash byte escapes in the Python-only name PNG fallback and WinRT warmup, and in the new synthetic test frame. Those created incorrect byte sequences. Corrected the byte literals, prevented caching empty OCR reads, rejected ambiguous ellipsized competing names, and excluded visibly sold rows from the name-only highlight path. Added targeted regression cases. **The updated Windows tests and live OCR have not been executed yet**; do not mark the branch qualified.

## Next acceptance gate

Use independently labeled **native-resolution** shop screenshots (not consecutive OBS frames), test cold and warm names, and time the actual installed Windows scanner end-to-end. Report false positives, missed items, P50/P95/max for queue-to-overlay and scan-start-to-overlay, plus the number of unique shops. Keep original main and all historical files unchanged.
