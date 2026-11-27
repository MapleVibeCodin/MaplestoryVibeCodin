# FIX-005-Missing-Highlight: Shop item fails to highlight or name mismatches

Status: **Open**

250 inventory timing records: all fallback geometry/name-only; 129 OCR scans, one candidate-bearing locked attempt, no verified unique match. Exact cause unknown (wrong shop, OCR mismatch, tooltip, sold row, room/focus loss). Status diagnostics added in https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/456b90748e6440870b4f0ea9cbc475210c8b5c0e/The%20ultimate%20beast/fm_sprint.py and feedback; do not infer exact OCR names from status. Existing scanner gates https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/shop_inventory.py and https://github.com/MapleVibeCodin/MaplestoryVibeCodin/blob/a80a9ffbcc2a4a1616b5cfdc8c91b35c430df8fb/Scanner%20Nov%2020/fm_rush.py. Regression: native labeled shop evidence, exact target/name comparison, no stale/wrong item highlight, maintain strict scroll guards. Historical 70 tests do not prove live highlighting. No verified fix; use future actual diagnostic evidence, do not rerun unchanged research.

Update this record with each recurrence, actual check results, and the new commit. Never overwrite historical evidence.


## Centered live evidence
2026-11-27 Centered: 239 inventory scans, 124 OCR, median total 29.2ms; six ROW_CHECK name-only candidate diagnostic states across three locked attempts. Candidate is not a verified correct item or purchase. No new recognition correction; open.


## Spatial live trial evidence
Spatial session: 478 inventory scans, 267 OCR, median total 31.63ms, 467 fallback geometry, 11 exact geometry, all name_only. Diagnostic states: 37 target not visible, 14 verifying, 2 ROW_CHECK name-only candidate events (one lock), 1 strict scroll geometry wait; zero verified unique matches. Pinned shop_inventory.py explicitly rejects strict scroll on fallback geometry and exact-name fast path abstains on no match; no actual row text or screenshots in archive, cannot identify wrong shop vs OCR mismatch. Next: labeled shop captures, verified geometry and item recognition regression, no relaxed matching.


## Stable candidate
2a6a083553dcdd4f0e1f9e95729a2c87c7bff052: retained name-only fast hit path; a name-only miss now falls through to the pinned full-row recognition, exact price checks, alternate sold contrast and post-capture revalidation. Strict scroll/fallback geometry guards retained; no seller OCR or automatic inputs. Structural checks only, actual OCR accuracy and performance still open. Session shop captures restored to permit independent verification.
