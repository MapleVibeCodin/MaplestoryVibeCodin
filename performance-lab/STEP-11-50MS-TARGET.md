# Step 11 — 50ms name-first target

**Branch:** `performance-lab/step-11-50ms-target`  
**Base:** Step 10 commit `c2791e685463cbd499f163df8dde991f2f08dd78`

## Objective
Once the FM shop is visible, identify the unique exact item name and draw an amber row box as fast as possible. No seller, price, stats, purchase click or mouse movement is part of this fast target path.

## Changes
- Compact OCR only the six 158×20 name bands, excluding seller/price/stat pixels. Six rows produce 474×480 OCR pixels vs prior 486×804 (about 42% fewer pixels).
- Prewarm the persistent Windows OCR process in the background at tracker startup.
- Cache row-name recognition by the name-band pixels only. Price changes do not invalidate this cache.
- One native observation/capture per shop scan, reusing Step 10 anchor/geometry evidence.
- Exact, unique full normalized item-name match only. No fuzzy match, truncated name, tooltip-covered row, or duplicate match.
- Immediate `ROW_CHECK` amber overlay. Name-only is not price/stats verified and never green. No automatic click.
- Active scan cadence 5ms; GUI polling 10ms while the FM room-title gate is confirmed; 50ms outside the room.
- Scroll targets keep the previous strict OCR/contrast verification path.
- Telemetry now records `shop_gate_ms`, `name_ocr_ms`, `queue_to_target_ms`, `shop_open_to_target_ms`, `target_to_overlay_ms`, `shop_open_to_overlay_ms`, `queue_to_overlay_ms`, cache hits/misses, and p95 distributions.

Historical geometry check: inspected the name-band crops across 16 archived shop screenshots; the 20px crop contains the item-name glyphs and excludes the price line. Raw images remain private and are not committed.

## 50ms qualification
Target: **P95 shop-open-to-visible-overlay ≤ 50ms**. Also require P95 `queue_to_overlay_ms` ≤ 40ms to reserve up to 10ms for the UI polling phase. These are target thresholds, not achieved results.

The timer begins when the worker scan starts (includes shop gate/capture); the queue-to-overlay timer begins when a scan is queued. UI room/shop detection polls every 10ms when target/game focus is valid, so the real shop-opening moment between polls is bounded approximately by that cadence but is not directly timestamped. The overlay's `show_many` invokes its draw/follow synchronously; telemetry timestamp is immediately after that call.

Cold unseen item-name OCR can still exceed 50ms. The fast path is expected to be fastest on exact cached name rows. No 50ms guarantee until measured on the user's Windows machine. If cold OCR P95 fails, next iteration is pixel-template/glyph matching trained from archived, OCR-verified item rows—do not add fuzzy recognition.

## Tests to run (targeted, no unnecessary replay)
1. `py -3 -m py_compile shop_inventory.py fm_rush.py performance_recorder.py`
2. `test_fast_target.py` (new)
3. `test_item_first.py` (Step 10)
4. `test_speed_equivalence.py` (Step 9)
5. `test_inventory_hover.py` (recognition/tooltip/geometry regression)
6. `test_performance_recorder.py` (timing telemetry/regression)

The previous 174 Windows regression pass belongs to Step 8 cleanup; do not claim it validates this new runtime branch.

## Live benchmark
Run 30 shop-open samples with one target listing; include cache-cold and cache-warm items. Export the performance report JSON and inspect P50/P95/max for `shop_open_to_overlay_ms` and `queue_to_overlay_ms`, plus OCR vs cache distributions. If P95 is over threshold, retain the data and optimize only the measured bottleneck.

## Integrity
Isolated branch/worktree. No production deployment or merge. Preserve historical screenshots/videos, calibrations, old code, pre-optimized backup and all prior checkpoint branches.